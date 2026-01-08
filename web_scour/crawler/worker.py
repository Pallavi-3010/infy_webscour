import pika        # communicate with RabbitMQ
import requests    # fetch web pages
import os
import time
from multiprocessing import Process, Manager 
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

QUEUE_NAME = "url_queue"

# ---------------- PRODUCER ----------------
def producer(seed_url):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=seed_url
    )

    print(f"[PRODUCER] Seed URL added -> {seed_url}")
    connection.close()


# ---------------- WORKER ----------------
def worker(worker_id, max_pages, global_counter, lock):
    visited = set()

    if not os.path.exists("pages"):
        os.makedirs("pages")

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost")
    )
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    def crawl(ch, method, properties, body):
        url = body.decode()

        # ---------------- PAGE SAFETY ----------------
        with lock:
            if global_counter.value >= max_pages:
                print(f"[WORKER-{worker_id}] MAX_PAGES reached. Stopping worker")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                ch.stop_consuming()
                return

            # Reserve page number
            global_counter.value += 1
            page_number = global_counter.value

        if url in visited:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(f"[WORKER-{worker_id}] Crawling => {url}")

        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                print(f"[WORKER-{worker_id}] FETCH FAILED")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                with lock:
                    global_counter.value -= 1
                return

            filename = f"pages/page{page_number}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)

            print(f"[SAVED] {filename}")

            visited.add(url)

            # Extract same-domain links
            soup = BeautifulSoup(response.text, "html.parser")
            base_domain = urlparse(url).netloc

            for link in soup.find_all("a", href=True):
                new_url = urljoin(url, link["href"])
                parsed = urlparse(new_url)

                if parsed.scheme in ["http", "https"] and parsed.netloc == base_domain:
                    channel.basic_publish(
                        exchange="",
                        routing_key=QUEUE_NAME,
                        body=new_url
                    )

        except Exception as e:
            print(f"[WORKER-{worker_id}] FETCH FAILED")
            with lock:
                global_counter.value -= 1

        print(f"[WORKER-{worker_id}] ACK => {url}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=crawl)
    channel.start_consuming()
    connection.close()


# ---------------- MAIN ----------------
if __name__ == "__main__":
    seed_url = input("Enter Seed URL: ").strip()
    total_workers = int(input("Enter Total Workers: "))
    max_pages = int(input("Enter Max Pages to Crawl: "))

    if not os.path.exists("pages"):
        os.makedirs("pages")

    manager = Manager()
    global_counter = manager.Value("i", 0)
    lock = manager.Lock()

    start_time = time.time()

    # ---------------- PRODUCER ----------------
    producer(seed_url)

    # ---------------- START WORKERS ----------------
    processes = []
    for i in range(1, total_workers + 1):
        p = Process(
            target=worker,
            args=(i, max_pages, global_counter, lock)
        )
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    # ---------------- FINAL SUMMARY ----------------
    end_time = time.time()
    print("\n========== SUMMARY ==========")
    print("Number of workers used  :", total_workers)
    print("Total pages crawled     :", global_counter.value)
    print("Total time taken (sec)  :", round(end_time - start_time, 2))
    print("=============================")
