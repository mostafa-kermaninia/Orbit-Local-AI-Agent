from __future__ import annotations

import math
from typing import Any


def draw_orbit_hud(
    canvas: Any,
    *,
    width: int,
    height: int,
    phase: float,
    state: str,
    assistant_name: str,
    state_color: str,
    text_color: str,
) -> None:
    """Draw a typography-safe, responsive ORBIT core.

    Layer order is deliberate:
      1) background grid/scanner
      2) outer animated rings/nodes
      3) opaque core armor
      4) typography
      5) waveform outside the largest ring

    No animated primitive can cross the title/state safe-zone.
    """
    c = canvas
    w = max(1, int(width))
    h = max(1, int(height))
    cx = w / 2
    cy = h * 0.45
    c.delete("all")

    pulse = (math.sin(phase * 1.8) + 1.0) / 2.0

    # Background grid.
    spacing = 46 if w >= 760 else 38
    offset = int((phase * 4) % spacing)

    for x in range(-spacing + offset, w + spacing, spacing):
        c.create_line(x, 0, x, h, fill="#07171E", width=1)
    for y in range(-spacing + offset, h + spacing, spacing):
        c.create_line(0, y, w, y, fill="#07171E", width=1)

    # Scanner is drawn behind all HUD geometry.
    scan_y = (h * 0.10) + (
        (math.sin(phase * 0.55) + 1) / 2
    ) * (h * 0.78)
    c.create_line(
        w * 0.10,
        scan_y,
        w * 0.90,
        scan_y,
        fill="#0A2D37",
        width=1,
    )

    # Corner target marks.
    min_dim = min(w, h)
    margin = max(22, min(32, int(min_dim * 0.06)))
    arm = max(30, min(44, int(min_dim * 0.078)))

    for x1, y1, sx, sy in [
        (margin, margin, 1, 1),
        (w - margin, margin, -1, 1),
        (margin, h - margin, 1, -1),
        (w - margin, h - margin, -1, -1),
    ]:
        c.create_line(
            x1,
            y1,
            x1 + sx * arm,
            y1,
            fill="#15505F",
            width=2,
        )
        c.create_line(
            x1,
            y1,
            x1,
            y1 + sy * arm,
            fill="#15505F",
            width=2,
        )

    # Significantly larger than the old 17% / 132px cap.
    base = max(
        106.0,
        min(
            172.0,
            min_dim * 0.235,
            w * 0.16,
        ),
    )
    outer_r = base * 1.72

    # Horizon lines stop before the animated ring area.
    gap = outer_r + 28
    c.create_line(
        w * 0.12,
        cy,
        max(w * 0.12, cx - gap),
        cy,
        fill="#0D3540",
        width=1,
    )
    c.create_line(
        min(w * 0.88, cx + gap),
        cy,
        w * 0.88,
        cy,
        fill="#0D3540",
        width=1,
    )

    # Segmented animated rings.
    rings = [
        (base * 1.72, 2.0, 54, 3),
        (base * 1.48, -2.7, 72, 2),
        (base * 1.26, 3.5, 40, 2),
    ]

    for radius, speed, extent, line_width in rings:
        start = (phase * speed * 18) % 360
        for index in range(4):
            angle = start + index * 90
            c.create_arc(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                start=angle,
                extent=extent,
                style="arc",
                outline=(
                    state_color
                    if index % 2 == 0
                    else "#176173"
                ),
                width=line_width,
            )

    # Engineering ticks.
    for degree in range(0, 360, 30):
        angle = math.radians(degree)
        r1 = base * 1.56
        r2 = base * 1.62
        c.create_line(
            cx + math.cos(angle) * r1,
            cy + math.sin(angle) * r1,
            cx + math.cos(angle) * r2,
            cy + math.sin(angle) * r2,
            fill="#155465",
            width=1,
        )

    # Orbiting telemetry nodes.
    for index in range(8):
        angle = (
            phase * (0.52 if index % 2 else -0.42)
            + index * math.tau / 8
        )
        radius = base * (
            1.42 if index % 2 else 1.64
        )
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        node_r = 3 if index % 3 else 5
        c.create_oval(
            x - node_r,
            y - node_r,
            x + node_r,
            y + node_r,
            fill=state_color,
            outline="",
        )

    def hex_points(
        radius: float,
        angle_shift: float = 0.0,
    ) -> list[float]:
        points: list[float] = []
        for index in range(6):
            angle = (
                angle_shift
                + math.radians(60 * index - 30)
            )
            points.extend(
                [
                    cx + math.cos(angle) * radius,
                    cy + math.sin(angle) * radius,
                ]
            )
        return points

    # Opaque armor guarantees a clean text safe-zone.
    c.create_polygon(
        hex_points(
            base * 1.03,
            phase * 0.035,
        ),
        outline="#1B7182",
        fill="#04151B",
        width=2,
    )
    c.create_polygon(
        hex_points(
            base * 0.78,
            -phase * 0.055,
        ),
        outline=state_color,
        fill="#061D25",
        width=3,
    )

    c.create_oval(
        cx - base * 0.54,
        cy - base * 0.54,
        cx + base * 0.54,
        cy + base * 0.54,
        fill="#06171E",
        outline="#81EFF8",
        width=1,
    )

    glow = base * (0.405 + 0.025 * pulse)
    c.create_oval(
        cx - glow,
        cy - glow,
        cx + glow,
        cy + glow,
        fill="#082A34",
        outline=state_color,
        width=2,
    )

    halo = base * 0.31
    c.create_oval(
        cx - halo,
        cy - halo,
        cx + halo,
        cy + halo,
        outline="#2E7D8D",
        width=1,
    )

    title_size = 31 if base >= 140 else 27
    state_size = 12 if base >= 125 else 10

    c.create_text(
        cx,
        cy - base * 0.09,
        text=assistant_name,
        fill=text_color,
        font=("Segoe UI", title_size, "bold"),
    )

    separator_y = cy + base * 0.055
    c.create_line(
        cx - base * 0.20,
        separator_y,
        cx + base * 0.20,
        separator_y,
        fill="#1B5663",
        width=1,
    )

    c.create_text(
        cx,
        cy + base * 0.23,
        text=state,
        fill=state_color,
        font=("Consolas", state_size, "bold"),
    )

    # Waveform lives completely outside the outer ring.
    active = state in {
        "LISTENING",
        "TRANSCRIBING",
        "THINKING",
        "SPEAKING",
    }
    energy = 28 if active else 8

    desired_bar_y = cy + outer_r + 20
    bar_y = min(h - 28, desired_bar_y)
    available = max(8.0, h - bar_y - 8)
    energy = min(energy, available * 1.65)

    for index in range(-17, 18):
        x = cx + index * 8
        value = abs(
            math.sin(
                phase * 2.2 + index * 0.61
            )
            * math.cos(
                phase * 0.7 + index * 0.19
            )
        )
        bar_height = 4 + value * energy
        c.create_line(
            x,
            bar_y - bar_height / 2,
            x,
            bar_y + bar_height / 2,
            fill=(
                state_color
                if abs(index) < 11
                else "#176173"
            ),
            width=3,
        )
