import os
from typing import TypeVar

from flask import Flask, current_app
import requests
from prometheus_client import Counter, Gauge, generate_latest, CollectorRegistry
from flask_apscheduler import APScheduler

NEZHA_TOKEN = os.getenv('NP_NEZHA_TOKEN')
NEZHA_URL = os.getenv('NP_NEZHA_URL')
NP_NAMESPACE = os.getenv('NP_NAMESPACE', 'nezha_server')
NP_UPDATE_INTERVAL = 5


T = TypeVar('T', Counter, Gauge)


class Metric:
    registry = CollectorRegistry()

    def __init__(self):
        self.metrics = []

        self.add('last_active', Gauge, 'active', unit='time')
        self.add('host.BootTime', Gauge, 'boot', unit='time')
        self.add('status.Uptime', Gauge, 'up', unit='time')

        self.add('status.CPU', Gauge, 'cpu', unit='percent')
        self.add('status.Load1', Gauge, 'load1')
        self.add('status.Load5', Gauge, 'load5')
        self.add('status.Load15', Gauge, 'load15')

        self.add('host.MemTotal', Gauge, 'memory_total', unit='bytes')
        self.add('status.MemUsed', Gauge, 'memory_used', unit='bytes')
        self.add('host.DiskTotal', Gauge, 'disk_total', unit='bytes')
        self.add('status.DiskUsed', Gauge, 'disk_used', unit='bytes')
        self.add('host.SwapTotal', Gauge, 'swap_total', unit='bytes')
        self.add('status.SwapUsed', Gauge, 'swap_used', unit='bytes')

        self.add('status.NetInTransfer', Gauge, 'network_rx_total', unit='bytes')
        self.add('status.NetOutTransfer', Gauge, 'network_tx_total', unit='bytes')
        self.add('status.NetInSpeed', Gauge, 'network_rx_speed', unit='bytes')
        self.add('status.NetOutSpeed', Gauge, 'network_tx_speed', unit='bytes')
        self.add('status.TcpConnCount', Gauge, 'network_tcp_connection', unit='count')
        self.add('status.UdpConnCount', Gauge, 'network_udp_connection', unit='count')
        self.add('status.ProcessCount', Gauge, 'process', unit='count')

        self.info_metric = self.create_metric(Gauge, 'info',
                                              labelnames=['name', 'platform', 'platform_version',
                                                          'arch', 'country_code'])

    def update(self, data: dict):
        name = data.get('name')
        for metric, key in self.metrics:
            d = data.copy()
            for k in key.split('.'):
                if k not in d:
                    raise KeyError(f'no found: {key}')
                d = d.get(k)    # type: ignore
            if not isinstance(d, (int, float)):
                raise ValueError()
            if isinstance(metric, Gauge):
                metric.labels(name=name).set(d)
            elif isinstance(metric, Counter):
                metric.labels(name=name)._raise_if_not_observable()
                metric.labels(name=name)._value.set(d)

        host = data.get('host', {})
        self.info_metric.labels(name=name, platform=host.get('Platform'), platform_version=host.get('PlatformVersion'),
                                arch=host.get('Arch'), country_code=host.get('CountryCode')).set(1)

    def add(self, nz_key: str, *args, **kwargs):
        metric = self.create_metric(*args, **kwargs)
        self.metrics.append((metric, nz_key))

    @classmethod
    def create_metric(cls, metric_type: type[T], name: str, doc: str = '', **kwargs):
        metric_args = dict(labelnames=['name'], namespace=NP_NAMESPACE, registry=cls.registry)
        metric_args.update(**kwargs)
        return metric_type(name, doc, **metric_args)  # type: ignore


def update_metrics(app: Flask, metric: Metric) -> None:
    with app.app_context():
        try:
            res = requests.get(f'{NEZHA_URL}/api/v1/server/details',
                               headers={'Authorization': NEZHA_TOKEN})
            res.raise_for_status()
            data = res.json()
            for srv in data.get('result', []):
                if 'name' not in srv or 'host' not in srv or 'status' not in srv:
                    continue
                metric.update(srv)
        except Exception as e:
            current_app.logger.warning(f'update metric fail: {e}')


def create_app():
    app = Flask(__name__)
    metric = Metric()
    scheduler = APScheduler()
    scheduler.add_job('update_metrics', update_metrics, args=(app, metric),
                      trigger='interval', seconds=NP_UPDATE_INTERVAL,
                      replace_existing=True)
    scheduler.start()
    update_metrics(app, metric)
    return app


app = create_app()


@app.route('/')
@app.route('/metrics')
def view_metric():
    return (generate_latest(Metric.registry), 200, {'Content-Type': 'text/plain; charset=utf-8',
                                                    'Connection': 'close'})
