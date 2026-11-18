#!/usr/bin/env python3
"""
Editorial Gold Dashboard Generator for Home Assistant
=====================================================
Generates Desktop (Haupt-Home), Tablet, and Mobile Lovelace dashboards
featuring the custom:editorial-hero-card and animated custom:golden-streams-card
from a single portable JSON project configuration.

Usage:
  python3 generate_dashboards.py configs/sascha_home.json --out-dir ./output
  python3 generate_dashboards.py configs/sascha_home.json --apply --ha-dir /opt/homeassistant
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

RESOURCE_URL = "/local/editorial-gold/golden-streams-card.js?v=1"
RESOURCE_ID = "editorial_gold_golden_streams_v1"

CREAM_CARD_MOD = {
    "style": {
        ".": (
            ":host {\n"
            "  --primary-text-color: #181c22 !important;\n"
            "  --secondary-text-color: #5c4f3d !important;\n"
            "  --card-primary-color: #181c22 !important;\n"
            "  --card-secondary-color: #5c4f3d !important;\n"
            "  --ha-color-text-primary: #181c22 !important;\n"
            "  --ha-color-text-secondary: #5c4f3d !important;\n"
            "  --rgb-amber: 181, 137, 45 !important;\n"
            "  --rgb-state-light: 181, 137, 45 !important;\n"
            "  --mush-rgb-amber: 181, 137, 45 !important;\n"
            "  --mush-rgb-state-light: 181, 137, 45 !important;\n"
            "  --slider-color: #b5892d !important;\n"
            "  --slider-bg-color: rgba(181, 137, 45, 0.22) !important;\n"
            "}\n"
            "ha-card {\n"
            "  background: linear-gradient(145deg, #f5ecd9 0%, #eadbc0 100%) !important;\n"
            "  border: 1px solid #c59b5f !important;\n"
            "  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25) !important;\n"
            "}\n"
        ),
        "mushroom-state-info$": (
            ".primary {\n"
            "  color: #181c22 !important;\n"
            "  font-weight: 600 !important;\n"
            "}\n"
            ".secondary {\n"
            "  color: #5c4f3d !important;\n"
            "}\n"
        ),
    }
}

VOICE_DARK_GOLD_MOD = {
    "style": {
        ".": (
            ":host {\n"
            "  --primary-text-color: #f3ead8 !important;\n"
            "  --secondary-text-color: #e6c978 !important;\n"
            "  --card-primary-color: #f3ead8 !important;\n"
            "  --card-secondary-color: #e6c978 !important;\n"
            "}\n"
            "ha-card {\n"
            "  background: linear-gradient(135deg, #242b35 0%, #171c23 100%) !important;\n"
            "  border: 1px solid #d4af37 !important;\n"
            "}\n"
        ),
        "mushroom-state-info$": (
            ".primary {\n"
            "  color: #f3ead8 !important;\n"
            "  font-weight: 600 !important;\n"
            "}\n"
            ".secondary {\n"
            "  color: #e6c978 !important;\n"
            "}\n"
        ),
    }
}


def build_chips(cfg: dict, mode: str = "tablet") -> dict:
    """mode: 'desktop' | 'tablet' | 'mobile'"""
    hdr = cfg["header"]
    net = cfg.get("network", {})
    all_lights = [l["entity"] for r in cfg["rooms"] for l in r.get("lights", []) if l.get("hero", True)]
    all_dw = [d["entity"] for d in cfg.get("security", {}).get("doors_windows", [])]

    lights_expr = (
        "{{ [" + ", ".join(f"states('{e}')" for e in all_lights) + "] "
        "| select('eq', 'on') | list | count }}"
    )
    dw_expr = (
        "{% set c = [" + ", ".join(f"states('{e}')" for e in all_dw) + "] "
        "| select('eq', 'on') | list | count %}"
        "{{ c ~ ' offen' if c > 0 else 'Alles zu' }}"
    )
    dw_color_expr = (
        "{% set c = [" + ", ".join(f"states('{e}')" for e in all_dw) + "] "
        "| select('eq', 'on') | list | count %}"
        "{{ 'red' if c > 0 else 'green' }}"
    )

    chips = [
        {
            "type": "weather",
            "entity": hdr["weather"]["entity"],
            "show_temperature": True,
            "show_conditions": mode != "mobile",
        },
        {
            "type": "template",
            "icon": "mdi:lightbulb-group",
            "icon_color": "{% if (" + lights_expr + " | int) > 0 %}amber{% else %}grey{% endif %}",
            "content": lights_expr + (" an" if mode == "mobile" else " Lichter an"),
            "tap_action": {"action": "navigate", "navigation_path": "raeume"},
        },
        {
            "type": "template",
            "icon": "mdi:shield-home-outline",
            "icon_color": dw_color_expr,
            "content": dw_expr,
            "tap_action": {"action": "navigate", "navigation_path": "status"},
        },
    ]

    if hdr.get("phone_battery"):
        chips.append(
            {
                "type": "entity",
                "entity": hdr["phone_battery"]["entity"],
                "icon": "mdi:cellphone-charging",
                "icon_color": "amber",
            }
        )

    if mode in ("tablet", "desktop") and net.get("wan_status"):
        chips.append(
            {
                "type": "entity",
                "entity": net["wan_status"],
                "name": "WAN",
                "icon": "mdi:web-check",
                "icon_color": "green",
            }
        )

    if hdr.get("voice"):
        chips.append(
            {
                "type": "template",
                "icon": "mdi:microphone-outline",
                "icon_color": "amber",
                "content": "Assist",
                "tap_action": {"action": "assist", "start_listening": True},
            }
        )

    return {
        "type": "custom:mushroom-chips-card",
        "alignment": "center" if mode == "mobile" else "start",
        "chips": chips,
    }


def make_hero_card(cfg: dict, subtitle: str) -> dict:
    return {
        "type": "custom:editorial-hero-card",
        "title": cfg["project_title"].upper(),
        "badge": "Editorial Gold",
        "user_name": cfg["header"]["person"]["name"],
        "subtitle": subtitle,
    }


def make_golden_streams_card(cfg: dict, height: int = 330) -> dict:
    hdr = cfg["header"]
    sec = cfg.get("security", {})
    net = cfg.get("network", {})
    all_lights = [l["entity"] for r in cfg["rooms"] for l in r.get("lights", []) if l.get("hero", True)]
    all_dw = [d["entity"] for d in sec.get("doors_windows", [])]
    all_motion = [m["entity"] for m in sec.get("motion", [])]

    nodes = []
    if net.get("download_speed"):
        nodes.append(
            {
                "label": "Internet-Durchsatz",
                "subtitle": "FRITZ!Box 7520 Download",
                "entity": net["download_speed"],
            }
        )
    if all_lights:
        nodes.append(
            {
                "label": "Beleuchtung",
                "subtitle": "Aktive Lampen im Zuhause",
                "entity": all_lights[0],
                "type": "lights_count",
                "entities": all_lights,
            }
        )
    if all_dw:
        nodes.append(
            {
                "label": "Türen & Fenster",
                "subtitle": "Alle Kontakt-Sensoren",
                "entity": all_dw[0],
                "type": "doors_count",
                "entities": all_dw,
            }
        )
    if all_motion:
        nodes.append(
            {
                "label": "Bewegung & Präsenz",
                "subtitle": "Flur · Küche · WoZi · Terrasse",
                "entity": all_motion[0],
                "type": "motion_count",
                "entities": all_motion,
            }
        )
    if hdr.get("backup"):
        nodes.append(
            {
                "label": "System & Backup",
                "subtitle": "Zigbee2MQTT & Sicherung",
                "entity": hdr["backup"]["entity"],
            }
        )

    return {
        "type": "custom:golden-streams-card",
        "title": "Golden Data Streams",
        "subtitle": f"Echtzeit-Telemetrie · {cfg['project_title']}",
        "height": height,
        "nodes": nodes,
    }


def make_light_card(light: dict, room_name: str, layout: str = "horizontal", cream: bool = True) -> dict:
    card = {
        "type": "custom:mushroom-light-card",
        "entity": light["entity"],
        "name": f"{light['name']}" if room_name.lower() in light["name"].lower() else f"{room_name} · {light['name']}",
        "icon": light.get("icon", "mdi:lightbulb-outline"),
        "layout": layout,
        "fill_container": True,
        "use_light_color": False,
        "show_brightness_control": light.get("dimmable", True),
        "show_color_control": light.get("color", False),
        "collapsible_controls": True,
        "icon_color": "amber",
    }
    if cream:
        card["card_mod"] = CREAM_CARD_MOD
    return card


def make_media_card(mp: dict, compact: bool = False) -> dict:
    return {
        "type": "custom:mushroom-media-player-card",
        "entity": mp["entity"],
        "name": mp["name"],
        "icon": mp.get("icon", "mdi:speaker"),
        "layout": "horizontal",
        "fill_container": True,
        "use_media_info": True,
        "show_volume_level": True,
        "volume_controls": ["volume_mute", "volume_buttons"] if compact else ["volume_set", "volume_mute"],
        "media_controls": ["on_off", "play_pause_stop"] if compact else ["on_off", "play_pause_stop", "next"],
        "collapsible_controls": True,
    }


def make_rooms_view(cfg: dict, max_columns: int = 3) -> dict:
    theme = cfg["theme"]
    room_sections = []
    for r in cfg["rooms"]:
        rcards = [{"type": "heading", "heading": r["name"], "heading_style": "title", "icon": r.get("icon", "mdi:door")}]
        for l in r.get("lights", []):
            rcards.append(make_light_card(l, r["name"], layout="horizontal", cream=True))
        for sw in r.get("switches", []):
            rcards.append(
                {
                    "type": "custom:mushroom-entity-card",
                    "entity": sw["entity"],
                    "name": sw["name"],
                    "icon": sw.get("icon", "mdi:toggle-switch-outline"),
                    "icon_color": "amber",
                    "tap_action": {"action": "toggle"},
                }
            )
        if r.get("sensors"):
            rcards.append(
                {
                    "type": "entities",
                    "state_color": True,
                    "entities": [{"entity": s["entity"], "name": s["name"]} for s in r["sensors"]],
                }
            )
        room_sections.append({"type": "grid", "cards": rcards})

    return {
        "path": "raeume",
        "title": "Räume",
        "icon": "mdi:floor-plan",
        "theme": theme,
        "type": "sections",
        "max_columns": max_columns,
        "sections": room_sections,
    }


def make_media_view(cfg: dict, max_columns: int = 3) -> dict:
    theme = cfg["theme"]
    media_sections = [
        {
            "type": "grid",
            "cards": [
                {"type": "heading", "heading": mp["name"], "heading_style": "title", "icon": mp.get("icon", "mdi:speaker")},
                {"type": "media-control", "entity": mp["entity"]},
            ],
        }
        for mp in cfg.get("media_players", [])
    ]
    if cfg.get("media_options"):
        media_sections.append(
            {
                "type": "grid",
                "cards": [
                    {"type": "heading", "heading": "Sonos Klang-Optionen", "heading_style": "title", "icon": "mdi:tune-vertical"},
                    {
                        "type": "entities",
                        "state_color": True,
                        "entities": [{"entity": o["entity"], "name": o["name"]} for o in cfg["media_options"]],
                    },
                ],
            }
        )

    return {
        "path": "medien",
        "title": "Medien",
        "icon": "mdi:music-box-multiple-outline",
        "theme": theme,
        "type": "sections",
        "max_columns": max_columns,
        "sections": media_sections,
    }


def make_status_view(cfg: dict, max_columns: int = 3) -> dict:
    theme = cfg["theme"]
    hdr = cfg["header"]
    net = cfg.get("network", {})
    sec = cfg.get("security", {})

    status_sections = []
    if net:
        net_entities = [
            {"entity": net["wan_status"], "name": "Internet (WAN)"},
            {"entity": net["guest_wifi"], "name": "Gast-WLAN"},
            {"entity": net["wifi_24"], "name": "WLAN 2,4 GHz"},
            {"entity": net["wifi_5"], "name": "WLAN 5 GHz"},
            {"entity": hdr["zigbee_bridge"]["entity"], "name": "Zigbee2MQTT Bridge"},
        ]
        if hdr["zigbee_bridge"].get("permit_join"):
            net_entities.append({"entity": hdr["zigbee_bridge"]["permit_join"], "name": "Zigbee Anlernen (Permit Join)"})
        for key, label in (("external_ip", "Externe IP"), ("cpu_temp", "FRITZ!Box Temperatur"), ("uptime", "FRITZ!Box Betriebszeit")):
            if net.get(key):
                net_entities.append({"entity": net[key], "name": label})

        status_sections.append(
            {
                "type": "grid",
                "cards": [
                    {"type": "heading", "heading": "Netzwerk & FRITZ!Box", "heading_style": "title", "icon": "mdi:router-wireless"},
                    {"type": "entities", "state_color": True, "entities": net_entities},
                    {
                        "type": "history-graph",
                        "title": "Durchsatz (24h)",
                        "hours_to_show": 24,
                        "entities": [
                            {"entity": net["download_speed"], "name": "Download"},
                            {"entity": net["upload_speed"], "name": "Upload"},
                        ],
                    },
                ],
            }
        )

    if sec:
        sec_cards = [{"type": "heading", "heading": "Sicherheit & Sensoren", "heading_style": "title", "icon": "mdi:shield-check-outline"}]
        if sec.get("doors_windows"):
            sec_cards.append(
                {
                    "type": "entities",
                    "title": "Türen & Fenster",
                    "state_color": True,
                    "entities": [{"entity": dw["entity"], "name": dw["name"]} for dw in sec["doors_windows"]],
                }
            )
        if sec.get("motion"):
            sec_cards.append(
                {
                    "type": "entities",
                    "title": "Bewegungsmelder",
                    "state_color": True,
                    "entities": [{"entity": m["entity"], "name": m["name"]} for m in sec["motion"]],
                }
            )
        status_sections.append({"type": "grid", "cards": sec_cards})

    if cfg.get("batteries"):
        status_sections.append(
            {
                "type": "grid",
                "cards": [
                    {"type": "heading", "heading": "Batterien", "heading_style": "title", "icon": "mdi:battery-80"},
                    {
                        "type": "entities",
                        "state_color": True,
                        "entities": [{"entity": b["entity"], "name": b["name"]} for b in cfg["batteries"]],
                    },
                ],
            }
        )

    sys_entities = [{"entity": hdr["backup"]["entity"], "name": "Backup Status"}]
    if hdr["backup"].get("last_ok"):
        sys_entities.append({"entity": hdr["backup"]["last_ok"], "name": "Letztes Backup"})
    if hdr["backup"].get("next_run"):
        sys_entities.append({"entity": hdr["backup"]["next_run"], "name": "Nächstes Backup"})
    sys_entities.append({"entity": hdr["sun"]["entity"], "name": "Sonnenstand"})
    sys_entities.append({"entity": hdr["phone_battery"]["entity"], "name": "Handy Akku"})

    status_sections.append(
        {
            "type": "grid",
            "cards": [
                {"type": "heading", "heading": "Wetter & System", "heading_style": "title", "icon": "mdi:server-security"},
                {"type": "weather-forecast", "entity": hdr["weather"]["entity"], "forecast_type": "daily"},
                {"type": "entities", "entities": sys_entities},
            ],
        }
    )

    return {
        "path": "status",
        "title": "System",
        "icon": "mdi:shield-check-outline",
        "theme": theme,
        "type": "sections",
        "max_columns": max_columns,
        "sections": status_sections,
    }


def build_desktop_dashboard(cfg: dict) -> dict:
    """Haupt-Home Desktop: Links Fokus-Panel (Hero + Creme-Lichter + Assist), Rechts Golden Data Streams + Medien & Details."""
    theme = cfg["theme"]
    title = cfg["project_title"]
    hdr = cfg["header"]
    sec = cfg.get("security", {})
    net = cfg.get("network", {})

    all_lights = [l["entity"] for r in cfg["rooms"] for l in r.get("lights", []) if l.get("hero", True)]

    # Linke Spalte (1/3): Two-Tone Hero + Champagner-Creme Lichter + Hermes Voice
    left_cards = [
        make_hero_card(cfg, "Alle Räume, Lichter und Hermes Voice bereit."),
    ]
    for r in cfg["rooms"]:
        for l in r.get("lights", []):
            if not l.get("hero", True):
                continue
            left_cards.append(make_light_card(l, r["name"], layout="horizontal", cream=True))

    left_cards.append(
        {
            "type": "custom:mushroom-template-card",
            "primary": "Alle Lichter ausschalten",
            "secondary": "Schnell-Aktion für das gesamte Zuhause",
            "icon": "mdi:lightbulb-off-outline",
            "icon_color": "amber",
            "layout": "horizontal",
            "tap_action": {
                "action": "call-service",
                "service": "light.turn_off",
                "target": {"entity_id": all_lights},
            },
            "card_mod": CREAM_CARD_MOD,
        }
    )

    if hdr.get("voice"):
        left_cards.append(
            {
                "type": "custom:mushroom-template-card",
                "primary": hdr["voice"]["name"],
                "secondary": "Klicken zum Sprechen oder Frage stellen...",
                "icon": "mdi:microphone",
                "icon_color": "amber",
                "layout": "horizontal",
                "tap_action": {"action": "assist", "start_listening": True},
                "card_mod": VOICE_DARK_GOLD_MOD,
            }
        )

    # Rechte Spalte (2/3): Golden Data Streams + Medien + Sicherheit + Wetter/Netzwerk
    right_stream_cards = [
        make_golden_streams_card(cfg, height=340),
    ]

    # Sub-Grid direkt unter dem Golden Stream: Medien links, Sicherheit & Wetter rechts
    media_cards = [
        {"type": "heading", "heading": "Medien & Audio", "heading_style": "title", "icon": "mdi:speaker-multiple"},
        *[make_media_card(mp, compact=False) for mp in cfg.get("media_players", [])],
    ]
    if cfg.get("media_options"):
        media_cards.append(
            {
                "type": "entities",
                "title": "Sonos Klang",
                "state_color": True,
                "entities": [{"entity": o["entity"], "name": o["name"]} for o in cfg["media_options"][:3]],
            }
        )

    detail_cards = [
        {"type": "heading", "heading": "Türen, Fenster & Wetter", "heading_style": "title", "icon": "mdi:shield-check-outline"},
        {"type": "weather-forecast", "entity": hdr["weather"]["entity"], "forecast_type": "daily"},
    ]
    for al in sec.get("alarms", []):
        detail_cards.append(
            {
                "type": "custom:mushroom-entity-card",
                "entity": al["entity"],
                "name": al["name"],
                "icon": "mdi:smoke-detector-variant",
                "icon_color": "green",
            }
        )
    if sec.get("doors_windows"):
        detail_cards.append(
            {
                "type": "entities",
                "title": "Türen & Fenster",
                "state_color": True,
                "entities": [{"entity": dw["entity"], "name": dw["name"]} for dw in sec["doors_windows"]],
            }
        )
    if net:
        detail_cards.append(
            {
                "type": "history-graph",
                "title": "Internet-Durchsatz (24h)",
                "hours_to_show": 24,
                "entities": [
                    {"entity": net["download_speed"], "name": "Download"},
                    {"entity": net["upload_speed"], "name": "Upload"},
                ],
            }
        )
        detail_cards.append(
            {
                "type": "entities",
                "title": "Netzwerk-Schnellzugriff",
                "state_color": True,
                "entities": [
                    {"entity": net["wan_status"], "name": "Internet (WAN)"},
                    {"entity": net["guest_wifi"], "name": "Gast-WLAN"},
                    {"entity": hdr["zigbee_bridge"]["entity"], "name": "Zigbee2MQTT"},
                ],
            }
        )

    home_view = {
        "path": "home",
        "title": "Home",
        "icon": "mdi:home-outline",
        "theme": theme,
        "type": "sections",
        "max_columns": 3,
        "sections": [
            {"type": "grid", "column_span": 3, "cards": [build_chips(cfg, mode="desktop")]},
            {"type": "grid", "column_span": 1, "cards": left_cards},
            {"type": "grid", "column_span": 2, "cards": right_stream_cards},
            {"type": "grid", "column_span": 1, "cards": media_cards},
            {"type": "grid", "column_span": 2, "cards": detail_cards},
        ],
    }

    return {
        "title": title,
        "views": [
            home_view,
            make_rooms_view(cfg, max_columns=3),
            make_media_view(cfg, max_columns=3),
            make_status_view(cfg, max_columns=3),
        ],
    }


def build_tablet_dashboard(cfg: dict) -> dict:
    theme = cfg["theme"]
    title = cfg["project_title"]
    hdr = cfg["header"]
    sec = cfg.get("security", {})
    net = cfg.get("network", {})

    light_cards = [
        make_hero_card(cfg, "Tablet-Ansicht · Räume & Assist"),
    ]
    for r in cfg["rooms"]:
        for l in r.get("lights", []):
            if not l.get("hero", True):
                continue
            light_cards.append(make_light_card(l, r["name"], layout="horizontal", cream=True))

    if hdr.get("voice"):
        light_cards.append(
            {
                "type": "custom:mushroom-template-card",
                "primary": hdr["voice"]["name"],
                "secondary": "Tippen zum Sprechen oder Fragen",
                "icon": "mdi:microphone",
                "icon_color": "amber",
                "layout": "horizontal",
                "tap_action": {"action": "assist", "start_listening": True},
                "card_mod": VOICE_DARK_GOLD_MOD,
            }
        )

    media_cards = [
        make_golden_streams_card(cfg, height=270),
        {"type": "heading", "heading": "Medien & Netzwerk", "heading_style": "title", "icon": "mdi:speaker-multiple"},
        *[make_media_card(mp, compact=False) for mp in cfg.get("media_players", []) if mp.get("primary")],
    ]
    if net.get("guest_wifi"):
        media_cards.append(
            {
                "type": "custom:mushroom-entity-card",
                "entity": net["guest_wifi"],
                "name": "Gast-WLAN",
                "icon": "mdi:wifi-lock",
                "icon_color": "amber",
                "tap_action": {"action": "toggle"},
            }
        )
    if sec.get("doors_windows"):
        media_cards.append(
            {
                "type": "entities",
                "title": "Türen & Fenster",
                "state_color": True,
                "entities": [{"entity": dw["entity"], "name": dw["name"]} for dw in sec["doors_windows"]],
            }
        )

    overview_view = {
        "path": "home",
        "title": "Übersicht",
        "icon": "mdi:home-outline",
        "theme": theme,
        "type": "sections",
        "max_columns": 3,
        "sections": [
            {"type": "grid", "column_span": 3, "cards": [build_chips(cfg, mode="tablet")]},
            {"type": "grid", "column_span": 1, "cards": light_cards},
            {"type": "grid", "column_span": 2, "cards": media_cards},
        ],
    }

    return {
        "title": title,
        "views": [
            overview_view,
            make_rooms_view(cfg, max_columns=3),
            make_media_view(cfg, max_columns=3),
            make_status_view(cfg, max_columns=3),
        ],
    }


def build_mobile_dashboard(cfg: dict) -> dict:
    theme = cfg["theme"]
    title = cfg["project_title"]
    hdr = cfg["header"]
    sec = cfg.get("security", {})
    net = cfg.get("network", {})

    quick_lights = []
    for r in cfg["rooms"]:
        for l in r.get("lights", []):
            if not l.get("hero", True):
                continue
            quick_lights.append(make_light_card(l, r["name"], layout="vertical", cream=True))

    mobile_home_cards = [
        make_hero_card(cfg, "Kompakte Mobil-Steuerung"),
        build_chips(cfg, mode="mobile"),
        {"type": "heading", "heading": "Schnellsteuerung", "heading_style": "title", "icon": "mdi:lightning-bolt-outline"},
        {"type": "grid", "columns": 2, "square": False, "cards": quick_lights},
    ]

    if hdr.get("voice"):
        mobile_home_cards.append(
            {
                "type": "custom:mushroom-template-card",
                "primary": "Hermes Assist starten",
                "secondary": "Sprachbefehl senden",
                "icon": "mdi:microphone",
                "icon_color": "amber",
                "layout": "horizontal",
                "tap_action": {"action": "assist", "start_listening": True},
                "card_mod": VOICE_DARK_GOLD_MOD,
            }
        )

    mobile_home_cards.append({"type": "heading", "heading": "Medien", "heading_style": "title", "icon": "mdi:speaker"})
    for mp in cfg.get("media_players", []):
        if mp.get("primary"):
            mobile_home_cards.append(make_media_card(mp, compact=True))

    mobile_home_cards.append(make_golden_streams_card(cfg, height=220))

    mobile_home_cards.append({"type": "heading", "heading": "Sicherheit & WLAN", "heading_style": "title", "icon": "mdi:shield-outline"})
    quick_sec_entities = []
    for dw in sec.get("doors_windows", [])[:2]:
        quick_sec_entities.append({"entity": dw["entity"], "name": dw["name"]})
    for al in sec.get("alarms", []):
        quick_sec_entities.append({"entity": al["entity"], "name": al["name"]})
    if net.get("guest_wifi"):
        quick_sec_entities.append({"entity": net["guest_wifi"], "name": "Gast-WLAN"})
    mobile_home_cards.append({"type": "entities", "state_color": True, "entities": quick_sec_entities})

    home_view = {
        "path": "home",
        "title": "Home",
        "icon": "mdi:home-outline",
        "theme": theme,
        "type": "sections",
        "max_columns": 1,
        "sections": [{"type": "grid", "cards": mobile_home_cards}],
    }

    return {
        "title": title,
        "views": [
            home_view,
            make_rooms_view(cfg, max_columns=1),
            make_media_view(cfg, max_columns=1),
            make_status_view(cfg, max_columns=1),
        ],
    }


def write_storage_file(path: Path, key: str, config: dict, backup: bool = False) -> None:
    if backup and path.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, path.parent / f"{path.name}.bak-{ts}")
    payload = {
        "version": 1,
        "minor_version": 1,
        "key": key,
        "data": {"config": config},
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def register_dashboards(storage_dir: Path, dashboards_meta: dict) -> None:
    reg_file = storage_dir / "lovelace_dashboards"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if reg_file.exists():
        shutil.copy2(reg_file, storage_dir / f"lovelace_dashboards.bak-{ts}")
        reg = json.loads(reg_file.read_text(encoding="utf-8"))
    else:
        reg = {"version": 1, "minor_version": 1, "key": "lovelace_dashboards", "data": {"items": []}}

    items = reg["data"]["items"]
    existing_by_id = {item["id"]: i for i, item in enumerate(items)}

    for key in ("desktop", "tablet", "mobile"):
        if key not in dashboards_meta:
            continue
        meta = dashboards_meta[key]
        entry = {
            "id": meta["id"],
            "icon": meta["icon"],
            "title": meta["title"],
            "url_path": meta["url_path"],
            "require_admin": False,
            "show_in_sidebar": True,
            "mode": "storage",
        }
        if meta["id"] in existing_by_id:
            items[existing_by_id[meta["id"]]] = entry
        else:
            items.append(entry)

    reg_file.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")


def register_resource(storage_dir: Path) -> None:
    res_file = storage_dir / "lovelace_resources"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if res_file.exists():
        shutil.copy2(res_file, storage_dir / f"lovelace_resources.bak-{ts}")
        res = json.loads(res_file.read_text(encoding="utf-8"))
    else:
        res = {"version": 1, "minor_version": 1, "key": "lovelace_resources", "data": {"items": []}}

    items = res["data"]["items"]
    if not any("golden-streams-card.js" in item.get("url", "") for item in items):
        items.append({"id": RESOURCE_ID, "url": RESOURCE_URL, "type": "module"})
    res_file.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Editorial Gold HA dashboards (Desktop, Tablet, Mobile).")
    parser.add_argument("config", help="Path to project config JSON (e.g. configs/sascha_home.json)")
    parser.add_argument("--out-dir", default="./output", help="Output directory for generated JSON files")
    parser.add_argument("--apply", action="store_true", help="Write directly into Home Assistant .storage")
    parser.add_argument("--ha-dir", default="/opt/homeassistant", help="Home Assistant config directory")
    args = parser.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    builders = {
        "desktop": build_desktop_dashboard,
        "tablet": build_tablet_dashboard,
        "mobile": build_mobile_dashboard,
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated = {}
    for key, builder in builders.items():
        if key in cfg["dashboards"]:
            d_id = cfg["dashboards"][key]["id"]
            d_cfg = builder(cfg)
            generated[d_id] = d_cfg
            write_storage_file(out_dir / f"lovelace.{d_id}", f"lovelace.{d_id}", d_cfg, backup=False)

    print(f"Generated {len(generated)} dashboards in {out_dir}")

    if args.apply:
        ha_dir = Path(args.ha_dir)
        storage_dir = ha_dir / ".storage"
        if not storage_dir.exists():
            print(f"ERROR: {storage_dir} not found", file=sys.stderr)
            return 1
        for d_id, d_cfg in generated.items():
            write_storage_file(storage_dir / f"lovelace.{d_id}", f"lovelace.{d_id}", d_cfg, backup=True)
        register_dashboards(storage_dir, cfg["dashboards"])
        register_resource(storage_dir)
        print(f"Applied dashboards, resources, and backups in {storage_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
