/**
 * Editorial Gold Suite for Home Assistant
 * Includes:
 *  1) custom:golden-streams-card  - Animated glowing golden Bezier particle streams
 *                                   connected to live Home Assistant entity nodes.
 *  2) custom:editorial-hero-card   - Signature two-tone (Anthracite Serif + Cream) header card.
 */

(function injectEditorialFonts() {
  if (document.getElementById("editorial-gold-fonts")) return;
  const link = document.createElement("link");
  link.id = "editorial-gold-fonts";
  link.rel = "stylesheet";
  link.href =
    "https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,500;0,600;0,700;1,400&family=Inter:wght@400;500;600;700&display=swap";
  document.head.appendChild(link);
})();

class GoldenStreamsCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = null;
    this._hass = null;
    this._particles = [];
    this._raf = null;
    this._resizeObserver = null;
    this._mounted = false;
  }

  static getStubConfig() {
    return {
      title: "Golden Data Streams",
      subtitle: "Echtzeit-Telemetrie",
      nodes: [],
    };
  }

  setConfig(config) {
    if (!config || !Array.isArray(config.nodes)) {
      throw new Error("golden-streams-card requires a 'nodes' array");
    }
    this._config = {
      title: config.title || "Golden Data Streams",
      subtitle: config.subtitle || "Live System- & Sensorströme",
      height: config.height || 340,
      nodes: config.nodes,
    };
    this._initParticles();
    if (this._mounted) this._renderNodes();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._mounted) {
      this._mount();
    }
    this._updateNodeValues();
  }

  connectedCallback() {
    if (this._mounted) this._startAnim();
  }

  disconnectedCallback() {
    this._stopAnim();
    if (this._resizeObserver) {
      this._resizeObserver.disconnect();
    }
  }

  getCardSize() {
    return 6;
  }

  _initParticles() {
    this._particles = [];
    const count = Math.max(36, this._config.nodes.length * 10);
    for (let i = 0; i < count; i++) {
      this._particles.push({
        streamIdx: i % Math.max(1, this._config.nodes.length),
        t: Math.random(),
        speed: 0.0018 + Math.random() * 0.0028,
        size: 1.2 + Math.random() * 2.2,
        offsetY: (Math.random() - 0.5) * 18,
        alpha: 0.45 + Math.random() * 0.55,
      });
    }
  }

  _mount() {
    this._mounted = true;
    const h = this._config.height;
    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }
        ha-card {
          position: relative;
          overflow: hidden;
          background: radial-gradient(circle at 28% 52%, rgba(212, 175, 55, 0.14) 0%, rgba(20, 25, 32, 0.96) 55%, #10141a 100%);
          border: 1px solid rgba(212, 175, 55, 0.35);
          border-radius: 16px;
          padding: 18px 20px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.42);
          font-family: 'Inter', var(--paper-font-body1_-_font-family, sans-serif);
          color: #f3ead8;
        }
        .header {
          position: relative;
          z-index: 2;
          display: flex;
          justify-content: space-between;
          align-items: baseline;
          margin-bottom: 10px;
          gap: 12px;
        }
        .title {
          font-family: 'EB Garamond', Georgia, serif;
          font-size: 22px;
          font-weight: 600;
          letter-spacing: 0.02em;
          color: #f3ead8;
        }
        .subtitle {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          color: #d4af37;
          opacity: 0.9;
        }
        .stage {
          position: relative;
          display: grid;
          grid-template-columns: 1fr 1.15fr;
          align-items: center;
          min-height: ${h}px;
          gap: 12px;
        }
        @media (max-width: 680px) {
          .stage {
            grid-template-columns: 1fr;
            min-height: auto;
          }
          canvas {
            opacity: 0.35;
          }
        }
        canvas {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          pointer-events: none;
          z-index: 1;
        }
        .nodes {
          grid-column: 2;
          position: relative;
          z-index: 2;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          gap: 10px;
        }
        @media (max-width: 680px) {
          .nodes {
            grid-column: 1;
          }
        }
        .node {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 10px;
          padding: 10px 14px;
          border-radius: 12px;
          background: rgba(18, 22, 28, 0.82);
          backdrop-filter: blur(8px);
          border: 1px solid rgba(212, 175, 55, 0.25);
          cursor: pointer;
          transition: border-color 0.2s ease, transform 0.15s ease, background 0.2s ease;
        }
        .node:hover {
          border-color: rgba(230, 201, 120, 0.75);
          background: rgba(28, 34, 44, 0.92);
          transform: translateX(2px);
        }
        .node-left {
          display: flex;
          align-items: center;
          gap: 10px;
          min-width: 0;
        }
        .dot {
          width: 9px;
          height: 9px;
          border-radius: 50%;
          background: #e6c978;
          box-shadow: 0 0 10px rgba(230, 201, 120, 0.95);
          flex-shrink: 0;
        }
        .dot.alert {
          background: #e57373;
          box-shadow: 0 0 10px rgba(229, 115, 115, 0.95);
        }
        .dot.ok {
          background: #81c784;
          box-shadow: 0 0 10px rgba(129, 199, 132, 0.85);
        }
        .meta {
          min-width: 0;
        }
        .node-label {
          font-size: 12px;
          font-weight: 600;
          color: #f3ead8;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .node-sub {
          font-size: 11px;
          color: #b8b2a6;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .node-right {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-shrink: 0;
        }
        .val {
          font-size: 12px;
          font-weight: 600;
          color: #e6c978;
          font-variant-numeric: tabular-nums;
        }
        .spark {
          width: 46px;
          height: 22px;
        }
      </style>
      <ha-card>
        <div class="header">
          <div class="title">${this._escape(this._config.title)}</div>
          <div class="subtitle">${this._escape(this._config.subtitle)}</div>
        </div>
        <div class="stage" id="stage">
          <canvas id="canvas"></canvas>
          <div class="nodes" id="nodes"></div>
        </div>
      </ha-card>
    `;

    this._renderNodes();
    this._setupCanvas();
    this._startAnim();
  }

  _escape(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  _renderNodes() {
    const container = this.shadowRoot.getElementById("nodes");
    if (!container) return;
    container.innerHTML = "";
    this._config.nodes.forEach((n, idx) => {
      const el = document.createElement("div");
      el.className = "node";
      el.dataset.idx = String(idx);
      const bars = [0.35, 0.7, 0.5, 0.9, 0.6, 0.8, 1.0]
        .map((r, bi) => {
          const x = bi * 6 + 2;
          const bh = Math.round(r * 16 + ((idx * 3 + bi) % 5));
          const y = 20 - Math.min(18, bh);
          return `<rect x="${x}" y="${y}" width="3.5" height="${Math.min(18, bh)}" rx="1.5" fill="url(#goldGrad)" opacity="${0.5 + r * 0.5}" />`;
        })
        .join("");

      el.innerHTML = `
        <div class="node-left">
          <span class="dot" id="dot-${idx}"></span>
          <div class="meta">
            <div class="node-label">${this._escape(n.label)}</div>
            <div class="node-sub" id="sub-${idx}">${this._escape(n.subtitle || "")}</div>
          </div>
        </div>
        <div class="node-right">
          <div class="val" id="val-${idx}">--</div>
          <svg class="spark" viewBox="0 0 46 22" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="goldGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#f3ead8"/>
                <stop offset="100%" stop-color="#c59b5f"/>
              </linearGradient>
            </defs>
            ${bars}
          </svg>
        </div>
      `;
      el.addEventListener("click", () => this._openMoreInfo(n.entity));
      container.appendChild(el);
    });
    this._updateNodeValues();
  }

  _openMoreInfo(entityId) {
    if (!entityId) return;
    const ev = new CustomEvent("hass-more-info", {
      bubbles: true,
      composed: true,
      detail: { entityId },
    });
    this.dispatchEvent(ev);
  }

  _updateNodeValues() {
    if (!this._hass || !this._config) return;
    this._config.nodes.forEach((n, idx) => {
      const valEl = this.shadowRoot.getElementById(`val-${idx}`);
      const subEl = this.shadowRoot.getElementById(`sub-${idx}`);
      const dotEl = this.shadowRoot.getElementById(`dot-${idx}`);
      if (!valEl || !dotEl) return;

      const st = this._hass.states[n.entity];
      if (!st) {
        valEl.textContent = "n/v";
        return;
      }

      let display = st.state;
      const unit = st.attributes.unit_of_measurement ? ` ${st.attributes.unit_of_measurement}` : "";

      if (n.type === "lights_count" && Array.isArray(n.entities)) {
        const onCount = n.entities.filter((id) => this._hass.states[id]?.state === "on").length;
        display = `${onCount} / ${n.entities.length} an`;
        dotEl.className = onCount > 0 ? "dot" : "dot ok";
      } else if (n.type === "doors_count" && Array.isArray(n.entities)) {
        const openCount = n.entities.filter((id) => this._hass.states[id]?.state === "on").length;
        display = openCount > 0 ? `${openCount} offen` : "Alles zu";
        dotEl.className = openCount > 0 ? "dot alert" : "dot ok";
      } else if (n.type === "motion_count" && Array.isArray(n.entities)) {
        const active = n.entities
          .filter((id) => this._hass.states[id]?.state === "on")
          .map((id) => this._hass.states[id]?.attributes?.friendly_name || id);
        display = active.length > 0 ? `${active.length} aktiv` : "Ruhig";
        if (subEl && active.length > 0) subEl.textContent = active.join(", ");
        else if (subEl) subEl.textContent = n.subtitle || "";
        dotEl.className = active.length > 0 ? "dot" : "dot ok";
      } else if (st.state === "on") {
        display = n.on_label || "Aktiv";
        dotEl.className = n.alert_on ? "dot alert" : "dot ok";
      } else if (st.state === "off") {
        display = n.off_label || "Aus / OK";
        dotEl.className = "dot ok";
      } else {
        const num = Number(st.state);
        if (!Number.isNaN(num) && unit) {
          display = `${num.toFixed(num >= 100 ? 0 : 1)}${unit}`;
        } else {
          display = `${st.state}${unit}`;
        }
        dotEl.className = "dot";
      }

      valEl.textContent = display;
    });
  }

  _setupCanvas() {
    const stage = this.shadowRoot.getElementById("stage");
    const canvas = this.shadowRoot.getElementById("canvas");
    if (!stage || !canvas) return;

    const resize = () => {
      const rect = stage.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.max(1, Math.floor(rect.width * dpr));
      canvas.height = Math.max(1, Math.floor(rect.height * dpr));
    };

    resize();
    this._resizeObserver = new ResizeObserver(resize);
    this._resizeObserver.observe(stage);
  }

  _cubicPoint(t, p0, p1, p2, p3) {
    const mt = 1 - t;
    const x =
      mt * mt * mt * p0.x +
      3 * mt * mt * t * p1.x +
      3 * mt * t * t * p2.x +
      t * t * t * p3.x;
    const y =
      mt * mt * mt * p0.y +
      3 * mt * mt * t * p1.y +
      3 * mt * t * t * p2.y +
      t * t * t * p3.y;
    return { x, y };
  }

  _startAnim() {
    if (this._raf) return;
    const draw = () => {
      this._drawFrame();
      this._raf = requestAnimationFrame(draw);
    };
    this._raf = requestAnimationFrame(draw);
  }

  _stopAnim() {
    if (this._raf) {
      cancelAnimationFrame(this._raf);
      this._raf = null;
    }
  }

  _drawFrame() {
    const canvas = this.shadowRoot.getElementById("canvas");
    const stage = this.shadowRoot.getElementById("stage");
    const nodeEls = this.shadowRoot.querySelectorAll(".node");
    if (!canvas || !stage || nodeEls.length === 0) return;

    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;
    const stageRect = stage.getBoundingClientRect();

    ctx.save();
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);

    // Subtle background constellation dots
    ctx.fillStyle = "rgba(212, 175, 55, 0.14)";
    for (let gx = 16; gx < w * 0.48; gx += 22) {
      for (let gy = 18; gy < h - 10; gy += 22) {
        if ((gx + gy) % 44 === 0) {
          ctx.beginPath();
          ctx.arc(gx, gy, 0.9, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }

    const origin = { x: 8, y: h * 0.52 };
    const curves = [];

    nodeEls.forEach((el, idx) => {
      const r = el.getBoundingClientRect();
      const target = {
        x: Math.max(40, r.left - stageRect.left + 8),
        y: r.top - stageRect.top + r.height / 2,
      };
      const cp1 = { x: origin.x + (target.x - origin.x) * 0.42, y: origin.y + (idx - (nodeEls.length - 1) / 2) * 14 };
      const cp2 = { x: origin.x + (target.x - origin.x) * 0.68, y: target.y };
      curves.push({ p0: origin, p1: cp1, p2: cp2, p3: target });

      // Draw soft golden glow line
      const grad = ctx.createLinearGradient(origin.x, origin.y, target.x, target.y);
      grad.addColorStop(0, "rgba(212, 175, 55, 0.08)");
      grad.addColorStop(0.55, "rgba(230, 201, 120, 0.35)");
      grad.addColorStop(1, "rgba(243, 234, 216, 0.65)");

      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(origin.x, origin.y);
      ctx.bezierCurveTo(cp1.x, cp1.y, cp2.x, cp2.y, target.x, target.y);
      ctx.stroke();
    });

    // Draw flowing golden particles
    for (const p of this._particles) {
      const c = curves[p.streamIdx % curves.length];
      if (!c) continue;
      p.t += p.speed;
      if (p.t > 1) p.t = 0;

      const pt = this._cubicPoint(p.t, c.p0, c.p1, c.p2, c.p3);
      const fade = Math.sin(p.t * Math.PI);
      const y = pt.y + p.offsetY * (1 - p.t) * fade;

      // Halo
      const glow = ctx.createRadialGradient(pt.x, y, 0, pt.x, y, p.size * 3.4);
      glow.addColorStop(0, `rgba(248, 232, 185, ${p.alpha * fade})`);
      glow.addColorStop(0.5, `rgba(212, 175, 55, ${p.alpha * fade * 0.4})`);
      glow.addColorStop(1, "rgba(212, 175, 55, 0)");

      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(pt.x, y, p.size * 3.4, 0, Math.PI * 2);
      ctx.fill();

      // Core spark
      ctx.fillStyle = `rgba(255, 248, 225, ${p.alpha * fade})`;
      ctx.beginPath();
      ctx.arc(pt.x, y, p.size * 0.75, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.restore();
  }
}

class EditorialHeroCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
    this._hass = null;
    this._rendered = false;
  }

  setConfig(config) {
    this._config = config || {};
    if (this._rendered) this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._rendered = true;
      this._render();
    }
    this._updateGreeting();
  }

  getCardSize() {
    return 2;
  }

  _greeting() {
    const h = new Date().getHours();
    const name = this._config.user_name || "Sascha";
    if (h < 11) return `Guten Morgen, ${name}.`;
    if (h < 18) return `Guten Tag, ${name}.`;
    return `Guten Abend, ${name}.`;
  }

  _render() {
    const title = this._config.title || "SASCHA'S HOME";
    const badge = this._config.badge || "Editorial Gold";
    const sub = this._config.subtitle || "Steuerung, Räume und Assist auf einen Blick.";
    this.shadowRoot.innerHTML = `
      <style>
        ha-card {
          background: linear-gradient(160deg, #1b222c 0%, #131820 100%);
          border: 1px solid rgba(212, 175, 55, 0.42);
          border-radius: 16px;
          padding: 20px 22px 18px 22px;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
          color: #f3ead8;
        }
        .row {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: 12px;
          flex-wrap: wrap;
        }
        .title {
          font-family: 'EB Garamond', Georgia, serif;
          font-size: 28px;
          font-weight: 600;
          letter-spacing: 0.04em;
          color: #f3ead8;
        }
        .badge {
          font-family: 'EB Garamond', Georgia, serif;
          font-size: 14px;
          color: #d4af37;
          letter-spacing: 0.04em;
        }
        .greet {
          margin-top: 6px;
          font-family: 'EB Garamond', Georgia, serif;
          font-size: 16px;
          color: #e6dfd0;
          line-height: 1.4;
        }
        .sub {
          margin-top: 2px;
          font-family: 'Inter', sans-serif;
          font-size: 12px;
          color: #a9a296;
        }
      </style>
      <ha-card>
        <div class="row">
          <div class="title">${title}</div>
          <div class="badge">${badge}</div>
        </div>
        <div class="greet" id="greet">${this._greeting()}</div>
        <div class="sub">${sub}</div>
      </ha-card>
    `;
  }

  _updateGreeting() {
    const el = this.shadowRoot?.getElementById("greet");
    if (el) el.textContent = this._greeting();
  }
}

if (!customElements.get("golden-streams-card")) {
  customElements.define("golden-streams-card", GoldenStreamsCard);
}
if (!customElements.get("editorial-hero-card")) {
  customElements.define("editorial-hero-card", EditorialHeroCard);
}

window.customCards = window.customCards || [];
window.customCards.push(
  {
    type: "golden-streams-card",
    name: "Golden Data Streams Card",
    description: "Animated glowing golden Bezier streams connected to live HA nodes",
  },
  {
    type: "editorial-hero-card",
    name: "Editorial Hero Card",
    description: "Two-tone Editorial Gold serif header card",
  }
);

