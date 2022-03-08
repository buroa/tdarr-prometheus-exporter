"""Application exporter"""

import re
import os
import time
import requests

from prometheus_client import start_http_server, Gauge

class AppMetrics:
    """
    Representation of Prometheus metrics and loop to fetch and transform
    application metrics into Prometheus metrics.
    """

    def __init__(self, tdarr_api, polling_interval_seconds=5):
        self.tdarr_api = tdarr_api
        self.polling_interval_seconds = polling_interval_seconds

        # Prometheus metrics to collect
        self.worker = Gauge("tdarr_worker", "Nodes currently working", ['name', 'ip', 'port'])
        self.worker_limits = Gauge("tdarr_worker_limits", "Node worker limits", ['name', 'healthcheckcpu', 'healthcheckgpu', 'transcodecpu', 'transcodegpu'])
        self.processing = Gauge("tdarr_processing", "File currently processing", ['name', 'worker_type', 'file'])
        self.total_file_count = Gauge("tdarr_total_file_count", "The total file count")
        self.total_transcode_count = Gauge("tdarr_total_transcode_count", "The total transcoded count")
        self.total_health_count = Gauge("tdarr_total_health_count", "The total health count")
        self.size_diff = Gauge("tdarr_size_diff", "The size difference")

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            self.fetch_workers()
            self.fetch_cruddb()
            time.sleep(self.polling_interval_seconds)

    def fetch_workers(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """

        # Fetch raw status data from the application
        dvr = requests.get(url = f"{self.tdarr_api}/api/v2/get-nodes")
        status_data = dvr.json()

        # Clear the old metrics
        self.worker.clear()
        self.worker_limits.clear()
        self.processing.clear()

        # For each activity, grap the ip address and channel
        for worker, var in status_data.items():
            ip = var.get('ip')
            port = var.get('port')
            limits = var.get('workerLimits', {})
            workers = var.get('workers', {})
            
            # lets export it
            self.worker.labels(
                name = worker,
                ip = ip,
                port = port
            ).set(1)
            self.worker_limits.labels(
                name = worker,
                healthcheckcpu = limits.get('healthcheckcpu'),
                healthcheckgpu = limits.get('healthcheckgpu'),
                transcodecpu = limits.get('transcodecpu'),
                transcodegpu = limits.get('transcodegpu')
            ).set(1)

            for _, var in workers.items():
                worker_type = var.get('workerType')
                file = var.get('file')
                self.processing.labels(
                    name = worker,
                    worker_type = worker_type,
                    file = file
                ).set(1)

    def fetch_cruddb(self):
        """
        Get metrics from application and refresh Prometheus metrics with
        new values.
        """

        # Fetch raw status data from the application
        dvr = requests.post(
            url = f"{self.tdarr_api}/api/v2/cruddb",
            json = {
                "data": {
                    "collection": "StatisticsJSONDB",
                    "mode": "getAll"
                }
            }
        )
        status_data = dvr.json()[0]

        self.total_file_count.set(status_data.get('totalFileCount', 0))
        self.total_transcode_count.set(status_data.get('totalTranscodeCount', 0))
        self.total_health_count.set(status_data.get('totalHealthCheckCount', 0))
        self.size_diff.set(status_data.get('sizeDiff', 0))

def main():
    """Main entry point"""

    polling_interval_seconds = int(os.getenv("POLLING_INTERVAL_SECONDS", "5"))
    exporter_port = int(os.getenv("EXPORTER_PORT", "9877"))
    tdarr_api = os.getenv("TDARR_API", "http://localhost:8089")

    app_metrics = AppMetrics(
        tdarr_api=tdarr_api,
        polling_interval_seconds=polling_interval_seconds
    )
    start_http_server(exporter_port)
    app_metrics.run_metrics_loop()

if __name__ == "__main__":
    main()