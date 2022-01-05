import requests


class Grafana(object):

    def __init__(self, url: str, api_key: str) -> None:
        self.session: requests.Session = requests.Session()
        self.session.headers = {"Authorization": f"Bearer {api_key}"}
        self.url = url
        self.identifier = 2

    @classmethod
    def load_grafana(cls, url):
        r = requests.post(
            f"http://admin:admin@{url}/api/orgs", json={"name": "starlink"})
        response = r.json()
        org_id = response['orgId']
        r = requests.post(
            f"http://admin:admin@{url}/api/users/using/{org_id}")
        r = requests.post(f"http://admin:admin@{url}/api/auth/keys",
                          json={"name": "starlink_api", "role": "Admin"})
        api_key = r.json()["key"]
        return Grafana(url, api_key)

    def get_identifier(self):
        self.identifier += 1
        return self.identifier

    def reset_identifier(self):
        self.identifier = 2

    def set_redis(self, url: str, password: str):
        r = self.session.post(f"http://{self.url}/api/datasources", json={
            "name": "Redis0",
            "type": "redis-datasource",
            "url": url,
            "access": "proxy",
            "typeLogoUrl": "public/plugins/redis-datasource/img/logo.svg",
            "user": "",
            "password": password,
            "secureJsonData": {
                "password": password,
            },
            "basicAuth": False,
            "isDefault": True,
            "readOnly": False,
        })
        return r.content

    def add_dashboard_slice(self, s, system):
        self.reset_identifier()
        refId = ["A", "B", "C", "D", "E", "F", "G", "H"]
        name = f"Slice {s.identity} - {s.name.upper()}"
        dashboard = {
            "annotations": {
                "list": [
                    {
                        "builtIn": 1,
                        "datasource": "Redis0",
                        "enable": True,
                        "hide": True,
                        "iconColor": "rgba(0, 211, 255, 1)",
                        "name": "Annotations & Alerts",
                        "target": {
                            "limit": 100,
                            "matchAny": False,
                            "tags": [],
                            "type": "dashboard"
                        },
                        "type": "dashboard"
                    }
                ]
            },
            "editable": True,
            "fiscalYearStartMonth": 0,
            "gnetId": None,
            "graphTooltip": 0,
            "id": None,
            "uid": None,
            "links": [],
            "liveNow": True,
            "panels": [
                {
                    "collapsed": False,
                    "datasource": None,
                    "gridPos": {
                        "h": 1,
                        "w": 24,
                        "x": 0,
                        "y": 0
                    },
                    "id": self.get_identifier(),
                    "panels": [],
                    "title": "Key Performance Indicators (KPIs)",
                    "type": "row"
                },
                {
                    "datasource": None,
                    "description": "",
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisGridShow": True,
                                "axisLabel": "",
                                "axisPlacement": "left",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 20,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "smooth",
                                "lineStyle": {
                                    "fill": "solid"
                                },
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "area"
                                }
                            },
                            "mappings": [],
                            "min": 0,
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "transparent",
                                        "value": None
                                    }
                                ]
                            },
                            "unit": "Mbits"
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_kpis_upload_overconsumption"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "semi-dark-red",
                                            "mode": "fixed"
                                        }
                                    },
                                    {
                                        "id": "displayName",
                                        "value": "Overconsumption"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_kpis_upload"
                                },
                                "properties": [
                                    {
                                        "id": "displayName",
                                        "value": "Real Time Consumption"
                                    }
                                ]
                            }
                        ]
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 1
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "list",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "keyName": f"slice_{s.identity}_kpis_upload",
                            "legend": "",
                            "query": "",
                            "refId": "A",
                            "streaming": False,
                            "type": "timeSeries",
                            "value": ""
                        },
                        {
                            "command": "ts.range",
                            "hide": False,
                            "keyName": f"slice_{s.identity}_kpis_upload_overconsumption",
                            "legend": "",
                            "query": "",
                            "refId": "B",
                            "streaming": False,
                            "type": "timeSeries",
                            "value": ""
                        }
                    ],
                    "title": f"Upload Throughput ({s.kpi.upload} mbps)",
                    "transparent": True,
                    "type": "timeseries"
                },
                {
                    "datasource": None,
                    "description": "",
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisGridShow": True,
                                "axisLabel": "",
                                "axisPlacement": "left",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 20,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "smooth",
                                "lineStyle": {
                                    "fill": "solid"
                                },
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "line"
                                }
                            },
                            "mappings": [],
                            "min": 0,
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "transparent",
                                        "value": None
                                    }
                                ]
                            },
                            "unit": "Mbits"
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_kpis_download_overconsumption Download Throughput"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "semi-dark-red",
                                            "mode": "fixed"
                                        }
                                    },
                                    {
                                        "id": "displayName",
                                        "value": "Overconsumption"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_kpis_download Download Throughput"
                                },
                                "properties": [
                                    {
                                        "id": "displayName",
                                        "value": "Real Time Consumption"
                                    }
                                ]
                            }
                        ]
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 12,
                        "y": 1
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "list",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "keyName": f"slice_{s.identity}_kpis_download",
                            "legend": "",
                            "query": "",
                            "refId": "A",
                            "streaming": False,
                            "type": "timeSeries",
                            "value": "Download Throughput"
                        },
                        {
                            "command": "ts.range",
                            "hide": False,
                            "keyName": f"slice_{s.identity}_kpis_download_overconsumption",
                            "legend": "",
                            "query": "",
                            "refId": "B",
                            "streaming": False,
                            "type": "timeSeries",
                            "value": "Download Throughput"
                        }
                    ],
                    "title": f"Download Throughput ({s.kpi.download} mbps)",
                    "transparent": True,
                    "type": "timeseries"
                },
                {
                    "datasource": None,
                    "description": "",
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisGridShow": True,
                                "axisLabel": "",
                                "axisPlacement": "left",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 20,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "smooth",
                                "lineStyle": {
                                    "fill": "solid"
                                },
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "area"
                                }
                            },
                            "mappings": [],
                            "max": 100,
                            "min": 0,
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "transparent",
                                        "value": None
                                    }
                                ]
                            },
                            "unit": "percent"
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "PER"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "dark-red",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 9
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "hidden",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "keyName": f"slice_{s.identity}_kpis_per",
                            "legend": "",
                            "query": "",
                            "refId": "A",
                            "streaming": False,
                            "type": "timeSeries",
                            "value": "PER"
                        }
                    ],
                    "title": f"Packet Error Rate ({s.kpi.per}%)",
                    "transparent": True,
                    "type": "timeseries"
                },
                {
                    "datasource": None,
                    "description": "",
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisGridShow": True,
                                "axisLabel": "",
                                "axisPlacement": "left",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 20,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "smooth",
                                "lineStyle": {
                                    "fill": "solid"
                                },
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "line"
                                }
                            },
                            "mappings": [],
                            "max": 100,
                            "min": 0,
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "transparent",
                                        "value": None
                                    },
                                    {
                                        "color": "#EAB839",
                                        "value": 70
                                    }
                                ]
                            },
                            "unit": "ms"
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 12,
                        "y": 9
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "hidden",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "keyName": f"slice_{s.identity}_kpis_delay",
                            "legend": "",
                            "query": "",
                            "refId": "A",
                            "streaming": False,
                            "type": "timeSeries",
                            "value": "Latency"
                        }
                    ],
                    "title": f"Latency ({s.kpi.delay} ms)",
                    "transparent": True,
                    "type": "timeseries"
                },
                {
                    "collapsed": False,
                    "datasource": None,
                    "gridPos": {
                        "h": 1,
                        "w": 24,
                        "x": 0,
                        "y": 17
                    },
                    "id": self.get_identifier(),
                    "panels": [],
                    "title": "Measurement",
                    "type": "row"
                },
                {
                    "datasource": None,
                    "description": "",
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                }
                            },
                            "mappings": []
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_pdu_current"
                                },
                                "properties": [
                                    {
                                        "id": "displayName",
                                        "value": "Consumed PDU Sessions"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_pdu_left"
                                },
                                "properties": [
                                    {
                                        "id": "displayName",
                                        "value": "Available PDU Sessions"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_pdu_overconsumption"
                                },
                                "properties": [
                                    {
                                        "id": "displayName",
                                        "value": "Overconsumed PDU Sessions"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "Overconsumed PDU Sessions"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "semi-dark-red",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "Available PDU Sessions"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "#585858a8",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 18
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "displayLabels": [
                            "value"
                        ],
                        "legend": {
                            "displayMode": "table",
                            "placement": "right",
                            "values": [
                                "percent",
                                "value"
                            ]
                        },
                        "pieType": "donut",
                        "reduceOptions": {
                            "calcs": [
                                "lastNotNone"
                            ],
                            "fields": "",
                            "values": True
                        },
                        "tooltip": {
                            "mode": "single"
                        }
                    },
                    "repeat": None,
                    "targets": [
                        {
                            "command": "get",
                            "keyName": f"slice_{s.identity}_pdu_current",
                            "query": "",
                            "refId": "A",
                            "type": "command"
                        },
                        {
                            "command": "get",
                            "hide": False,
                            "keyName": f"slice_{s.identity}_pdu_left",
                            "query": "",
                            "refId": "B",
                            "type": "command"
                        },
                        {
                            "command": "get",
                            "hide": False,
                            "keyName": f"slice_{s.identity}_pdu_overconsumption",
                            "query": "",
                            "refId": "C",
                            "type": "command"
                        }
                    ],
                    "title": f"PDU Sessions ({s.max_pdu})",
                    "transparent": True,
                    "type": "piechart"
                },
                {
                    "datasource": None,
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "thresholds"
                            },
                            "mappings": [],
                            "min": 0,
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green",
                                        "value": None
                                    }
                                ]
                            },
                            "unit": "none"
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_resource_{r}"
                                },
                                "properties": [
                                    {
                                        "id": "displayName",
                                        "value": f"{r.upper()}"
                                    }
                                ]
                            } for r in system.resource_names
                        ]
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 12,
                        "y": 18
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "displayMode": "basic",
                        "orientation": "vertical",
                        "reduceOptions": {
                            "calcs": [],
                            "fields": "",
                            "limit": 25,
                            "values": True
                        },
                        "showUnfilled": True,
                        "text": {}
                    },
                    "pluginVersion": "8.2.2",
                    "targets": [
                        {
                            "command": "get",
                            "keyName": f"slice_{s.identity}_resource_{r}",
                            "query": "",
                            "refId": refId[i],
                            "type": "command"
                        } for i, r in enumerate(system.resource_names)
                    ],
                    "title": "Current Resource Consumption",
                    "transformations": [],
                    "transparent": True,
                    "type": "bargauge"
                },
            ],
            "refresh": "5s",
            "schemaVersion": 31,
            "style": "dark",
            "tags": [
                "templated"
            ],
            "templating": {
                "list": []
            },
            "time": {
                "from": "now-2m",
                "to": "now"
            },
            "timepicker": {
                "refresh_intervals": [
                    "5s",
                    "10s",
                    "30s",
                    "1m",
                    "5m",
                    "15m",
                    "30m",
                    "1h",
                    "2h",
                    "1d"
                ]
            },
            "timezone": "browser",
            "title": name,
            "version": 5
        }

        y = 18

        dashboard["panels"].extend(
            [
                {
                    "datasource": None,
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "bars",
                                "fillOpacity": 100,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "linear",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "normal"
                                },
                                "thresholdsStyle": {
                                    "mode": "off"
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green",
                                        "value": None
                                    }
                                ]
                            },
                            "unit": "short"
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_resource_{r}r_available"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "#585858a8",
                                            "mode": "fixed"
                                        }
                                    },
                                    {
                                        "id": "displayName",
                                        "value": "Available"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_resource_{r}r"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "semi-dark-blue",
                                            "mode": "fixed"
                                        }
                                    },
                                    {
                                        "id": "displayName",
                                        "value": "Consumed"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": f"slice_{s.identity}_resource_{r}r_overconsumption"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "semi-dark-red",
                                            "mode": "fixed"
                                        }
                                    },
                                    {
                                        "id": "displayName",
                                        "value": "Overconsumption"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "Available"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "#585858a8",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0 if i % 2 == 0 else 12,
                        "y": 26
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "list",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "keyName": f"slice_{s.identity}_resource_{r}r",
                            "query": "",
                            "refId": "A",
                            "type": "timeSeries",
                            "value": ""
                        },
                        {
                            "command": "ts.range",
                            "hide": False,
                            "keyName": f"slice_{s.identity}_resource_{r}r_available",
                            "query": "",
                            "refId": "B",
                            "type": "timeSeries"
                        },
                        {
                            "command": "ts.range",
                            "hide": False,
                            "keyName": f"slice_{s.identity}_resource_{r}r_overconsumption",
                            "query": "",
                            "refId": "C",
                            "type": "timeSeries"
                        }
                    ],
                    "title": f"{r.upper()} Consumption",
                    "transformations": [
                        {
                            "id": "concatenate",
                            "options": {}
                        }
                    ],
                    "transparent": True,
                    "type": "timeseries"
                } for i, r in enumerate(system.resource_names)
            ]
        )

        y += (len(system.resource_names) // 2 +
              len(system.resource_names) % 2) * 8 + 1

        for k, v in s.qfi.items():
            dashboard["panels"].extend(
                [
                    {
                        "collapsed": False,
                        "datasource": None,
                        "gridPos": {
                            "h": 1,
                            "w": 24,
                            "x": 0,
                            "y": y
                        },
                        "id": self.get_identifier(),
                        "panels": [],
                        "title": f"Quality of Service - {k.upper()}",
                        "type": "row"
                    },
                    {
                        "datasource": None,
                        "description": "",
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "palette-classic"
                                },
                                "custom": {
                                    "axisGridShow": False,
                                    "axisLabel": "",
                                    "axisPlacement": "left",
                                    "barAlignment": 0,
                                    "drawStyle": "line",
                                    "fillOpacity": 20,
                                    "gradientMode": "none",
                                    "hideFrom": {
                                        "legend": False,
                                        "tooltip": False,
                                        "viz": False
                                    },
                                    "lineInterpolation": "smooth",
                                    "lineStyle": {
                                        "fill": "solid"
                                    },
                                    "lineWidth": 2,
                                    "pointSize": 5,
                                    "scaleDistribution": {
                                        "type": "linear"
                                    },
                                    "showPoints": "auto",
                                    "spanNones": False,
                                    "stacking": {
                                        "group": "A",
                                        "mode": "none"
                                    },
                                    "thresholdsStyle": {
                                        "mode": "area"
                                    }
                                },
                                "mappings": [],
                                "max": 100,
                                "min": 0,
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {
                                            "color": "transparent",
                                            "value": None
                                        }
                                    ]
                                },
                                "unit": "percent"
                            },
                            "overrides": [
                                {
                                    "matcher": {
                                        "id": "byName",
                                        "options": "PER"
                                    },
                                    "properties": [
                                        {
                                            "id": "color",
                                            "value": {
                                                "fixedColor": "semi-dark-red",
                                                "mode": "fixed"
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        "gridPos": {
                            "h": 8,
                            "w": 12,
                            "x": 0,
                            "y": y + 8
                        },
                        "id": self.get_identifier(),
                        "options": {
                            "legend": {
                                "calcs": [],
                                "displayMode": "hidden",
                                "placement": "bottom"
                            },
                            "tooltip": {
                                "mode": "multi"
                            }
                        },
                        "targets": [
                            {
                                "command": "ts.range",
                                "keyName": f"slice_{s.identity}_qos_{k}_per",
                                "legend": "",
                                "query": "",
                                "refId": "A",
                                "streaming": False,
                                "type": "timeSeries",
                                "value": "PER"
                            }
                        ],
                        "title": f"Packet Error Rate ({v.per}%)",
                        "transparent": True,
                        "type": "timeseries"
                    },
                    {
                        "datasource": None,
                        "description": "",
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "palette-classic"
                                },
                                "custom": {
                                    "axisGridShow": True,
                                    "axisLabel": "",
                                    "axisPlacement": "left",
                                    "barAlignment": 0,
                                    "drawStyle": "line",
                                    "fillOpacity": 20,
                                    "gradientMode": "none",
                                    "hideFrom": {
                                        "legend": False,
                                        "tooltip": False,
                                        "viz": False
                                    },
                                    "lineInterpolation": "smooth",
                                    "lineStyle": {
                                        "fill": "solid"
                                    },
                                    "lineWidth": 2,
                                    "pointSize": 5,
                                    "scaleDistribution": {
                                        "type": "linear"
                                    },
                                    "showPoints": "auto",
                                    "spanNones": False,
                                    "stacking": {
                                        "group": "A",
                                        "mode": "none"
                                    },
                                    "thresholdsStyle": {
                                        "mode": "off"
                                    }
                                },
                                "mappings": [],
                                "min": 0,
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {
                                            "color": "transparent",
                                            "value": None
                                        }
                                    ]
                                },
                                "unit": "ms"
                            },
                            "overrides": []
                        },
                        "gridPos": {
                            "h": 8,
                            "w": 12,
                            "x": 12,
                            "y": y + 8
                        },
                        "id": self.get_identifier(),
                        "options": {
                            "legend": {
                                "calcs": [],
                                "displayMode": "hidden",
                                "placement": "bottom"
                            },
                            "tooltip": {
                                "mode": "multi"
                            }
                        },
                        "targets": [
                            {
                                "command": "ts.range",
                                "keyName": f"slice_{s.identity}_qos_{k}_pdb",
                                "legend": "",
                                "query": "",
                                "refId": "A",
                                "streaming": False,
                                "type": "timeSeries",
                                "value": "Latency"
                            }
                        ],
                        "title": f"Packet Delay Budget ({v.pdb} ms)",
                        "transparent": True,
                        "type": "timeseries"
                    }
                ]
            )
            y += 9

        r = self.session.post(f"http://{self.url}/api/dashboards/db", json={
            "dashboard": dashboard,
            "folderId": 0,
            "message": "Add new dashboard",
            "overwrite": True
        })
        return r.content

    def add_dashboard_system(self, slices, system):
        self.reset_identifier()
        refId = ["A", "B", "C", "D", "E", "F", "G", "H"]
        name = f"Starlink"

        d = {
            "annotations": {
                "list": [
                    {
                        "builtIn": 1,
                        "datasource": "Redis0",
                        "enable": True,
                        "hide": True,
                        "iconColor": "rgba(0, 211, 255, 1)",
                        "name": "Annotations & Alerts",
                        "target": {
                            "limit": 100,
                            "matchAny": False,
                            "tags": [],
                            "type": "dashboard"
                        },
                        "type": "dashboard"
                    }
                ]
            },
            "editable": True,
            "fiscalYearStartMonth": 0,
            "gnetId": None,
            "graphTooltip": 0,
            "id": None,
            "uid": None,
            "links": [],
            "liveNow": True,
            "panels": [
                {
                    "collapsed": False,
                    "datasource": None,
                    "gridPos": {
                        "h": 1,
                        "w": 24,
                        "x": 0,
                        "y": 0
                    },
                    "id": self.get_identifier(),
                    "panels": [],
                    "title": "System Monitoring",
                    "type": "row"
                },
                {
                    "datasource": None,
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "off"
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green",
                                        "value": None
                                    },
                                    {
                                        "color": "red",
                                        "value": 80
                                    }
                                ]
                            },
                            "unit": "Mbits"
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "system_resource_download"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "dark-yellow",
                                            "mode": "fixed"
                                        }
                                    },
                                    {
                                        "id": "displayName",
                                        "value": "Download"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "system_resource_upload"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "semi-dark-blue",
                                            "mode": "fixed"
                                        }
                                    },
                                    {
                                        "id": "displayName",
                                        "value": "Upload"
                                    }
                                ]
                            },
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "Download"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "semi-dark-green",
                                            "mode": "fixed"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 1
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "list",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "hide": False,
                            "keyName": "system_resource_download",
                            "query": "",
                            "refId": "B",
                            "type": "timeSeries"
                        },
                        {
                            "command": "ts.range",
                            "keyName": "system_resource_upload",
                            "query": "",
                            "refId": "A",
                            "type": "timeSeries"
                        }
                    ],
                    "title": "System Throughput",
                    "transparent": True,
                    "type": "timeseries"
                },
                {
                    "datasource": None,
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "off"
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green",
                                        "value": None
                                    },
                                    {
                                        "color": "red",
                                        "value": 80
                                    }
                                ]
                            },
                            "unit": "ms"
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "Value"
                                },
                                "properties": [
                                    {
                                        "id": "displayName",
                                        "value": "Latency"
                                    }
                                ]
                            }
                        ]
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 12,
                        "y": 1
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "hidden",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "keyName": "system_resource_latency",
                            "query": "",
                            "refId": "A",
                            "type": "timeSeries"
                        }
                    ],
                    "title": "Average Latency",
                    "transparent": True,
                    "type": "timeseries"
                },
                {
                    "datasource": None,
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "off"
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green",
                                        "value": None
                                    },
                                    {
                                        "color": "red",
                                        "value": 80
                                    }
                                ]
                            },
                            "unit": "percent"
                        },
                        "overrides": [
                            {
                                "matcher": {
                                    "id": "byName",
                                    "options": "Value"
                                },
                                "properties": [
                                    {
                                        "id": "color",
                                        "value": {
                                            "fixedColor": "semi-dark-red",
                                            "mode": "fixed"
                                        }
                                    },
                                    {
                                        "id": "displayName",
                                        "value": "Packet Error Rate"
                                    }
                                ]
                            }
                        ]
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 9
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "hidden",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "keyName": "system_resource_per",
                            "query": "",
                            "refId": "A",
                            "type": "timeSeries"
                        }
                    ],
                    "title": "Packet Error Rate",
                    "transparent": True,
                    "type": "timeseries"
                },
                {
                    "datasource": "-- Mixed --",
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "stepBefore",
                                "lineWidth": 1,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "off"
                                }
                            },
                            "mappings": [
                                {
                                    "options": {
                                        "0.5": {
                                            "index": 0,
                                            "text": "OFF"
                                        },
                                        "1.5": {
                                            "index": 1,
                                            "text": "ON"
                                        }
                                    },
                                    "type": "value"
                                }
                            ],
                            "max": 2,
                            "min": 0,
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green",
                                        "value": None
                                    }
                                ]
                            },
                            "unit": "short"
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 12,
                        "y": 9
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "hidden",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "datasource": "Redis0",
                            "keyName": "system_resource_resource_status",
                            "query": "",
                            "refId": "A",
                            "type": "timeSeries",
                            "value": "Resource Status"
                        }
                    ],
                    "title": "Auto-Scaler Status",
                    "transparent": True,
                    "type": "timeseries"
                },
                {
                    "collapsed": False,
                    "datasource": None,
                    "gridPos": {
                        "h": 1,
                        "w": 24,
                        "x": 0,
                        "y": 17
                    },
                    "id": self.get_identifier(),
                    "panels": [],
                    "title": "Resource Consumption",
                    "type": "row"
                },
            ],
            "refresh": "5s",
            "schemaVersion": 31,
            "style": "dark",
            "tags": [],
            "templating": {
                "list": []
            },
            "time": {
                "from": "now-2m",
                "to": "now"
            },
            "timepicker": {},
            "timezone": "browser",
            "title": name,
            "version": 34
        }

        for i, resource in enumerate(system.resource_names):
            d['panels'].extend(
                [
                    {
                        "datasource": None,
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "palette-classic"
                                },
                                "custom": {
                                    "axisLabel": "",
                                    "axisPlacement": "auto",
                                    "barAlignment": 0,
                                    "drawStyle": "line",
                                    "fillOpacity": 0,
                                    "gradientMode": "none",
                                    "hideFrom": {
                                        "legend": False,
                                        "tooltip": False,
                                        "viz": False
                                    },
                                    "lineInterpolation": "stepBefore",
                                    "lineStyle": {
                                        "fill": "solid"
                                    },
                                    "lineWidth": 2,
                                    "pointSize": 5,
                                    "scaleDistribution": {
                                        "type": "linear"
                                    },
                                    "showPoints": "auto",
                                    "spanNones": False,
                                    "stacking": {
                                        "group": "A",
                                        "mode": "normal"
                                    },
                                    "thresholdsStyle": {
                                        "mode": "off"
                                    }
                                },
                                "mappings": [],
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {
                                            "color": "green",
                                            "value": None
                                        },
                                        {
                                            "color": "red",
                                            "value": 80
                                        }
                                    ]
                                }
                            },
                            "overrides": [
                                {
                                    "matcher": {
                                        "id": "byName",
                                        "options": f"slice_{s.identity}_resource_{resource}r",
                                    },
                                    "properties": [
                                        {
                                            "id": "displayName",
                                            "value": f"Slice {s.identity} - {s.name.upper()}",
                                        }
                                    ]
                                } for s in slices
                            ]
                        },
                        "gridPos": {
                            "h": 8,
                            "w": 12,
                            "x": 0,
                            "y": 18
                        },
                        "id": self.get_identifier(),
                        "options": {
                            "legend": {
                                "calcs": [],
                                "displayMode": "list",
                                "placement": "bottom"
                            },
                            "tooltip": {
                                "mode": "multi"
                            }
                        },
                        "targets": [
                            {
                                "command": "ts.range",
                                "keyName": f"slice_{s.identity}_resource_{resource}r",
                                "query": "",
                                "refId": refId[j],
                                "type": "timeSeries",
                            } for j, s in enumerate(slices)
                        ],
                        "title": resource.upper(),
                        "transformations": [],
                        "transparent": True,
                        "type": "timeseries"
                    },
                    {
                        "datasource": None,
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "palette-classic"
                                },
                                "custom": {
                                    "axisLabel": "",
                                    "axisPlacement": "auto",
                                    "barAlignment": 0,
                                    "drawStyle": "line",
                                    "fillOpacity": 0,
                                    "gradientMode": "none",
                                    "hideFrom": {
                                        "legend": False,
                                        "tooltip": False,
                                        "viz": False
                                    },
                                    "lineInterpolation": "stepBefore",
                                    "lineStyle": {
                                        "fill": "solid"
                                    },
                                    "lineWidth": 2,
                                    "pointSize": 5,
                                    "scaleDistribution": {
                                        "type": "linear"
                                    },
                                    "showPoints": "auto",
                                    "spanNones": False,
                                    "stacking": {
                                        "group": "A",
                                        "mode": "normal"
                                    },
                                    "thresholdsStyle": {
                                        "mode": "line"
                                    }
                                },
                                "mappings": [],
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {
                                            "color": "green",
                                            "value": None
                                        },
                                        {
                                            "color": "red",
                                            "value": 2000
                                        }
                                    ]
                                }
                            },
                            "overrides": []
                        },
                        "gridPos": {
                            "h": 8,
                            "w": 12,
                            "x": 12,
                            "y": 18
                        },
                        "id": self.get_identifier(),
                        "options": {
                            "legend": {
                                "calcs": [],
                                "displayMode": "list",
                                "placement": "bottom"
                            },
                            "tooltip": {
                                "mode": "multi"
                            }
                        },
                        "targets": [
                            {
                                "command": "ts.range",
                                "keyName": f"slice_{s.identity}_resource_{resource}r",
                                "query": "",
                                "refId": refId[j],
                                "type": "timeSeries",
                                "value": f"Slice {s.identity} - {s.name.upper()}"
                            } for j, s in enumerate(slices)
                        ],
                        "title": f"{resource.upper()} Total",
                        "transformations": [
                            {
                                "id": "calculateField",
                                "options": {
                                    "alias": "Slices Total",
                                    "mode": "reduceRow",
                                    "reduce": {
                                        "reducer": "sum"
                                    },
                                    "replaceFields": True
                                }
                            }
                        ],
                        "transparent": True,
                        "type": "timeseries"
                    }
                ]
            )

        d['panels'].extend(
            [
                {
                    "collapsed": False,
                    "datasource": None,
                    "gridPos": {
                        "h": 1,
                        "w": 24,
                        "x": 0,
                        "y": 42
                    },
                    "id": self.get_identifier(),
                    "panels": [],
                    "title": "Key Performance Indicators (KPIs)",
                    "type": "row"
                },
                {
                    "datasource": None,
                    "description": "",
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "stepBefore",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "off"
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green",
                                        "value": None
                                    },
                                    {
                                        "color": "red",
                                        "value": 80
                                    }
                                ]
                            }
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 43
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "list",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "command": "ts.range",
                            "keyName": "system_slices",
                            "query": "",
                            "refId": "A",
                            "type": "timeSeries",
                            "value": "Slice"
                        }
                    ],
                    "title": "Slice Admission",
                    "transparent": True,
                    "type": "timeseries"
                },
                {
                    "datasource": None,
                    "description": "",
                    "fieldConfig": {
                        "defaults": {
                            "color": {
                                "mode": "palette-classic"
                            },
                            "custom": {
                                "axisLabel": "",
                                "axisPlacement": "auto",
                                "barAlignment": 0,
                                "drawStyle": "line",
                                "fillOpacity": 0,
                                "gradientMode": "none",
                                "hideFrom": {
                                    "legend": False,
                                    "tooltip": False,
                                    "viz": False
                                },
                                "lineInterpolation": "smooth",
                                "lineWidth": 2,
                                "pointSize": 5,
                                "scaleDistribution": {
                                    "type": "linear"
                                },
                                "showPoints": "auto",
                                "spanNones": False,
                                "stacking": {
                                    "group": "A",
                                    "mode": "none"
                                },
                                "thresholdsStyle": {
                                    "mode": "off"
                                }
                            },
                            "mappings": [],
                            "thresholds": {
                                "mode": "absolute",
                                "steps": [
                                    {
                                        "color": "green",
                                        "value": None
                                    },
                                    {
                                        "color": "red",
                                        "value": 80
                                    }
                                ]
                            },
                            "unit": "percent"
                        },
                        "overrides": []
                    },
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 12,
                        "y": 43
                    },
                    "id": self.get_identifier(),
                    "options": {
                        "legend": {
                            "calcs": [],
                            "displayMode": "list",
                            "placement": "bottom"
                        },
                        "tooltip": {
                            "mode": "multi"
                        }
                    },
                    "targets": [
                        {
                            "aggregation": "",
                            "command": "ts.range",
                            "keyName": f"total_{resource}_consumption",
                            "query": "",
                            "refId": refId[i],
                            "type": "timeSeries",
                            "value": resource.upper()
                        } for i, resource in enumerate(system.resource_names)
                    ],
                    "title": "Resource Consumption (%)",
                    "transparent": True,
                    "type": "timeseries"
                },
            ]
        )

        r = self.session.post(f"http://{self.url}/api/dashboards/db", json={
            "dashboard": d,
            "folderId": 0,
            # "folderUid": "General",
            "message": "Made changes to xyz",
            "overwrite": False
        })
        return r.content
