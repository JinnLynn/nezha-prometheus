# Nezha Prometheus

Convert [Nezha][] data to [Prometheus][] metrics.


## 使用

需通过环境变量配置：

* NEZHA_TOKEN: nezha [API Token](https://nezha.wiki/guide/api.html#%E5%88%9B%E5%BB%BA-token)，**必需**
* NEZHA_URL: nezha 访问地址，不包括api路径，如：https://status.example.com)，**必需**
* NP_NAMESPACE: prometheus metric 前缀，默认: nezha_server，**非必需**
* NP_UPDATE_INTERVAL: 读取API间隔，单位：秒， 默认： 5，**非必需**
* NP_AUTH_USR: basic auth username **非必需**
* NP_AUTH_PWD: basic auth password **非必需**


[Nezha]:        https://nezha.wiki/
[Prometheus]:   https://prometheus.io/
