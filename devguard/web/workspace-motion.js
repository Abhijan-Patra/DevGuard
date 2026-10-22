/* Decorative, local-only motion. Never receives prompts, clipboard or API data. */
(() => {
  "use strict";
  const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
  const finePointer = window.matchMedia("(pointer: fine)");
  const fields = new Map();
  let paused = false;

  class ShieldField {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext("2d");
      if (!this.ctx) return;
      this.frame = 0;
      this.visible = true;
      this.width = 0;
      this.height = 0;
      this.pointer = null;
      this.ripple = null;
      this.last = 0;
      this.points = [];
      this.handleMove = (event) => {
        if (!finePointer.matches || this.still()) return;
        const box = canvas.getBoundingClientRect();
        this.pointer = { x: event.clientX - box.left, y: event.clientY - box.top };
        this.wake();
      };
      this.handleLeave = () => { this.pointer = null; this.wake(); };
      this.handleDown = (event) => {
        if (this.still()) return;
        const box = canvas.getBoundingClientRect();
        this.ripple = { x: event.clientX - box.left, y: event.clientY - box.top, age: 0 };
        this.wake();
      };
      canvas.addEventListener("pointermove", this.handleMove);
      canvas.addEventListener("pointerleave", this.handleLeave);
      canvas.addEventListener("pointerdown", this.handleDown);
      this.resize = new ResizeObserver(() => this.layout());
      this.resize.observe(canvas);
      this.intersection = new IntersectionObserver(([entry]) => {
        this.visible = entry.isIntersecting;
        if (this.visible) this.wake(); else this.stop();
      });
      this.intersection.observe(canvas);
      canvas.dataset.ready = "true";
      this.layout();
    }

    still() { return paused || preference.matches; }

    layout() {
      const box = this.canvas.getBoundingClientRect();
      const width = Math.round(box.width), height = Math.round(box.height);
      if (!width || !height || (width === this.width && height === this.height)) return;
      this.width = width; this.height = height;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.canvas.width = Math.round(width * dpr);
      this.canvas.height = Math.round(height * dpr);
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const scale = Math.min(width / 290, height / 260);
      const cx = width / 2, cy = height / 2 - 3;
      this.points = [];
      // A procedural shield and check, sampled on a bounded grid. No image downloads.
      for (let gy = -17; gy <= 17; gy++) {
        for (let gx = -16; gx <= 16; gx++) {
          const x = gx / 16, y = gy / 17;
          const top = -0.82 + Math.abs(x) * 0.30;
          const bottom = 0.95 - Math.pow(Math.abs(x), 1.45) * 0.82;
          const inside = Math.abs(x) < 0.91 && y > top && y < bottom;
          if (!inside) continue;
          const edge = y < top + 0.15 || y > bottom - 0.15 || Math.abs(x) > 0.77;
          const tick = (x >= -0.43 && x < -0.08 && Math.abs(y - (x + 0.36)) < 0.11)
            || (x >= -0.12 && x < 0.49 && Math.abs(y - (-x + 0.16)) < 0.11);
          const hx = cx + x * 105 * scale, hy = cy + y * 112 * scale;
          const seed = Math.sin((gx + 19) * 12.9898 + (gy + 20) * 78.233);
          const offset = this.still() ? 0 : 12 + Math.abs(seed) * 34;
          this.points.push({ hx, hy, x: hx + x * offset, y: hy + y * offset,
            vx: 0, vy: 0, radius: (edge || tick ? 2.05 : 0.9) * scale,
            opacity: edge || tick ? 0.92 : 0.17 });
        }
      }
      this.pointer = null; this.ripple = null;
      this.colors();
      this.wake();
    }

    colors() {
      this.color = getComputedStyle(this.canvas).getPropertyValue("--accent").trim() || "#8ce8c1";
      this.wake();
    }

    wake() {
      if (this.frame || !this.ctx || !this.visible || document.hidden) return;
      this.frame = requestAnimationFrame((time) => this.draw(time));
    }

    draw(time) {
      this.frame = 0;
      if (!this.visible || document.hidden) return;
      const step = Math.min(2, Math.max(0.3, (time - (this.last || time - 16)) / 16.667));
      this.last = time;
      const still = this.still();
      this.ctx.clearRect(0, 0, this.width, this.height);
      this.ctx.fillStyle = this.color;
      if (this.ripple && !still) this.ripple.age += step * 16.667;
      let moving = false;
      for (const p of this.points) {
        if (still) { p.x = p.hx; p.y = p.hy; p.vx = p.vy = 0; }
        else {
          if (this.pointer) {
            const dx = p.x - this.pointer.x, dy = p.y - this.pointer.y;
            const distance = Math.hypot(dx, dy);
            if (distance < 65) {
              const force = (1 - distance / 65) * 1.4 * step;
              p.vx += dx / Math.max(distance, 1) * force;
              p.vy += dy / Math.max(distance, 1) * force;
            }
          }
          if (this.ripple && this.ripple.age < 750) {
            const dx = p.hx - this.ripple.x, dy = p.hy - this.ripple.y;
            const distance = Math.hypot(dx, dy);
            const band = Math.max(0, 1 - Math.abs(distance - this.ripple.age * 0.42) / 24);
            const force = band * (1 - this.ripple.age / 750) * 2 * step;
            p.vx += dx / Math.max(distance, 1) * force;
            p.vy += dy / Math.max(distance, 1) * force;
          }
          p.vx = (p.vx + (p.hx - p.x) * 0.045 * step) * Math.pow(0.83, step);
          p.vy = (p.vy + (p.hy - p.y) * 0.045 * step) * Math.pow(0.83, step);
          p.x += p.vx * step; p.y += p.vy * step;
          if (Math.abs(p.vx) + Math.abs(p.vy) > 0.015 || Math.hypot(p.x - p.hx, p.y - p.hy) > 0.1) moving = true;
          else { p.x = p.hx; p.y = p.hy; p.vx = p.vy = 0; }
        }
        this.ctx.globalAlpha = p.opacity;
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        this.ctx.fill();
      }
      this.ctx.globalAlpha = 1;
      if (this.ripple && this.ripple.age >= 750) this.ripple = null;
      if (!still && (moving || this.ripple)) this.wake();
    }

    stop() { cancelAnimationFrame(this.frame); this.frame = 0; this.last = 0; }
    reset() { this.pointer = null; this.ripple = null; this.stop(); this.wake(); }
    destroy() {
      this.stop();
      this.resize?.disconnect(); this.intersection?.disconnect();
      this.canvas.removeEventListener("pointermove", this.handleMove);
      this.canvas.removeEventListener("pointerleave", this.handleLeave);
      this.canvas.removeEventListener("pointerdown", this.handleDown);
    }
  }

  function sync() {
    const placeholders = [...document.querySelectorAll("canvas[data-shield-field]")];
    const keys = new Set(placeholders.map((canvas) => canvas.dataset.shieldField));
    for (const [key, field] of fields) {
      if (!keys.has(key)) { field.destroy(); fields.delete(key); }
    }
    for (const canvas of placeholders) {
      const key = canvas.dataset.shieldField;
      const existing = fields.get(key);
      if (existing) {
        if (canvas !== existing.canvas) canvas.replaceWith(existing.canvas);
        existing.layout();
      } else {
        // Cosmetic enhancement must never prevent access to operator controls.
        let field;
        try {
          field = new ShieldField(canvas);
          if (field.ctx) fields.set(key, field);
        } catch {
          field?.destroy();
          canvas.removeAttribute("data-ready");
        }
      }
    }
    updatePreference();
  }

  function updatePreference() {
    document.documentElement.dataset.motion = paused || preference.matches ? "off" : "on";
    for (const button of document.querySelectorAll('[data-action="motion"]')) {
      button.textContent = preference.matches ? "Reduced motion" : paused ? "Enable motion" : "Pause motion";
      button.setAttribute("aria-pressed", String(paused || preference.matches));
      button.disabled = preference.matches;
    }
  }
  function preferenceChanged() {
    updatePreference();
    for (const field of fields.values()) field.reset();
  }
  preference.addEventListener("change", preferenceChanged);
  document.addEventListener("visibilitychange", () => {
    document.documentElement.dataset.visibility = document.hidden ? "hidden" : "visible";
    for (const field of fields.values()) {
      if (document.hidden) field.stop(); else field.reset();
    }
  });
  document.documentElement.dataset.visibility = document.hidden ? "hidden" : "visible";
  const themeObserver = new MutationObserver(() => {
    for (const field of fields.values()) field.colors();
  });
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  window.DevGuardMotion = {
    sync,
    toggle() { paused = !paused; preferenceChanged(); },
    destroy() {
      for (const field of fields.values()) field.destroy();
      fields.clear();
    },
  };
  updatePreference();
})();
