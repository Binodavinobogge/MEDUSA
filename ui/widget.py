import math
import random

from PySide6.QtCore import (
    Qt,
    QPointF,
    QRectF,
    QTimer,
    Signal
)

from PySide6.QtGui import (
    QColor,
    QCursor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient
)

from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget
)

from core.network_monitor import (
    get_network_speed
)

from core.network_worker import (
    NetworkWorker
)


# =====================================================
# PALETTE MEDUSA
# =====================================================

CYAN = QColor("#59E8FF")
CYAN_BRIGHT = QColor("#8AF4FF")
CYAN_DARK = QColor("#1697B8")

PURPLE = QColor("#B66CFF")
PURPLE_DARK = QColor("#6C3DB2")

GREEN = QColor("#58F2AE")
YELLOW = QColor("#FFD064")
RED = QColor("#FF5A7F")

CREAM = QColor("#F4E8C9")

INK = QColor("#071218")

NAVY = QColor("#06151D")
NAVY_2 = QColor("#0A202A")
NAVY_3 = QColor("#0D2B36")

SKIN = QColor("#BEE4C7")
SKIN_SHADOW = QColor("#94C6A4")


# =====================================================
# UTILITY
# =====================================================

def format_speed(bytes_per_second):

    value = float(
        bytes_per_second
    )

    if value < 1024:
        return f"{value:.0f} B/s"

    value /= 1024

    if value < 1024:
        return f"{value:.1f} KB/s"

    value /= 1024

    if value < 1024:
        return f"{value:.2f} MB/s"

    value /= 1024

    return f"{value:.2f} GB/s"


# =====================================================
# ICONA SERVIZIO
# =====================================================

class ServiceIcon(QWidget):

    def __init__(
        self,
        service
    ):

        super().__init__()

        self.service = service

        self.status = "OFF"

        self.setFixedSize(
            36,
            36
        )

    # =================================================

    def set_status(
        self,
        status
    ):

        self.status = status

        self.update()

    # =================================================

    def get_color(self):

        if self.status == "ACTIVE":
            return GREEN

        if self.status == "LISTENING":
            return YELLOW

        if self.status == "SERVER_OFF":
            return PURPLE

        return QColor(
            "#7CA1AD"
        )

    # =================================================

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        color = self.get_color()

        # ---------------------------------------------
        # CERCHIO
        # ---------------------------------------------

        painter.setPen(
            QPen(
                QColor(
                    color.red(),
                    color.green(),
                    color.blue(),
                    120
                ),
                1.5
            )
        )

        painter.setBrush(
            QColor(
                8,
                31,
                41,
                210
            )
        )

        painter.drawEllipse(
            QRectF(
                1.5,
                1.5,
                33,
                33
            )
        )

        painter.setPen(
            QPen(
                color,
                2.2
            )
        )

        painter.setBrush(
            Qt.NoBrush
        )

        # ---------------------------------------------
        # HTTPS
        # ---------------------------------------------

        if self.service == "HTTPS":

            painter.drawRoundedRect(
                QRectF(
                    10,
                    15,
                    16,
                    13
                ),
                3,
                3
            )

            painter.drawArc(
                QRectF(
                    12,
                    8,
                    12,
                    13
                ),
                0,
                180 * 16
            )

        # ---------------------------------------------
        # DNS
        # ---------------------------------------------

        elif self.service == "DNS":

            painter.drawEllipse(
                QRectF(
                    8,
                    8,
                    20,
                    20
                )
            )

            painter.drawArc(
                QRectF(
                    12,
                    8,
                    12,
                    20
                ),
                90 * 16,
                180 * 16
            )

            painter.drawArc(
                QRectF(
                    12,
                    8,
                    12,
                    20
                ),
                270 * 16,
                180 * 16
            )

            painter.drawLine(
                8,
                18,
                28,
                18
            )

        # ---------------------------------------------
        # SMB
        # ---------------------------------------------

        elif self.service == "SMB":

            path = QPainterPath()

            path.moveTo(
                7,
                13
            )

            path.lineTo(
                14,
                13
            )

            path.lineTo(
                17,
                16
            )

            path.lineTo(
                29,
                16
            )

            path.lineTo(
                29,
                27
            )

            path.lineTo(
                7,
                27
            )

            path.closeSubpath()

            painter.drawPath(
                path
            )

        # ---------------------------------------------
        # RDP
        # ---------------------------------------------

        elif self.service == "RDP":

            painter.drawRoundedRect(
                QRectF(
                    7,
                    8,
                    22,
                    16
                ),
                2,
                2
            )

            painter.drawLine(
                18,
                24,
                18,
                29
            )

            painter.drawLine(
                13,
                29,
                23,
                29
            )

        # ---------------------------------------------
        # SSH
        # ---------------------------------------------

        else:

            font = QFont(
                "Consolas",
                12
            )

            font.setBold(
                True
            )

            painter.setFont(
                font
            )

            painter.drawText(
                self.rect(),
                Qt.AlignCenter,
                ">_"
            )


# =====================================================
# TENTACOLO PORTA
# =====================================================

class TentacleIndicator(QWidget):

    def __init__(self):

        super().__init__()

        self.setFixedSize(
            54,
            24
        )

        self.phase = 0.0

        self.status = "OFF"

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.animate
        )

        self.timer.start(
            45
        )

    # =================================================

    def set_status(
        self,
        status
    ):

        self.status = status

        self.update()

    # =================================================

    def animate(self):

        if self.status in (
            "ACTIVE",
            "LISTENING",
            "SERVER_OFF"
        ):

            self.phase += 0.15

            self.update()

    # =================================================

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        color = QColor(
            "#526C76"
        )

        amplitude = 1.0

        if self.status == "ACTIVE":

            color = CYAN

            amplitude = 4.2

        elif self.status == "LISTENING":

            color = YELLOW

            amplitude = 2.4

        elif self.status == "SERVER_OFF":

            color = PURPLE

            amplitude = 2.8

        pen = QPen(
            color,
            3.1
        )

        pen.setCapStyle(
            Qt.RoundCap
        )

        painter.setPen(
            pen
        )

        painter.setBrush(
            Qt.NoBrush
        )

        path = QPainterPath()

        path.moveTo(
            3,
            12
        )

        for x in range(
            3,
            49,
            4
        ):

            y = (
                12
                + math.sin(
                    x * 0.31
                    + self.phase
                )
                * amplitude
            )

            path.lineTo(
                x,
                y
            )

        painter.drawPath(
            path
        )

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            color
        )

        painter.drawEllipse(
            QPointF(
                49,
                12
            ),
            2.2,
            2.2
        )


# =====================================================
# TRAFFIC GRAPH
# =====================================================

class TrafficBars(QWidget):

    def __init__(self):

        super().__init__()

        self.download_history = [
            0.0
        ] * 28

        self.upload_history = [
            0.0
        ] * 28

        self.setMinimumHeight(
            50
        )

    # =================================================

    def add_sample(
        self,
        download,
        upload
    ):

        self.download_history.pop(
            0
        )

        self.upload_history.pop(
            0
        )

        self.download_history.append(
            float(download)
        )

        self.upload_history.append(
            float(upload)
        )

        self.update()

    # =================================================

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        combined = []

        for (
            download,
            upload
        ) in zip(
            self.download_history,
            self.upload_history
        ):

            combined.append(
                download
                + upload
            )

        peak = max(
            max(combined),
            1.0
        )

        count = len(
            combined
        )

        gap = 2.2

        width = max(
            2.0,
            (
                self.width()
                - gap * (
                    count - 1
                )
            )
            / count
        )

        for index, (
            download,
            upload
        ) in enumerate(
            zip(
                self.download_history,
                self.upload_history
            )
        ):

            total = (
                download
                + upload
            )

            ratio = min(
                1.0,
                total / peak
            )

            height = max(
                3.0,
                ratio
                * (
                    self.height()
                    - 5
                )
            )

            x = index * (
                width
                + gap
            )

            y = (
                self.height()
                - height
            )

            if download >= upload:

                color = CYAN

            else:

                color = PURPLE

            gradient = QLinearGradient(
                0,
                y,
                0,
                self.height()
            )

            gradient.setColorAt(
                0,
                color
            )

            gradient.setColorAt(
                1,
                QColor(
                    color.red(),
                    color.green(),
                    color.blue(),
                    120
                )
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                gradient
            )

            painter.drawRoundedRect(
                QRectF(
                    x,
                    y,
                    width,
                    height
                ),
                2,
                2
            )


# =====================================================
# SCENA MEDUSA
# =====================================================

class AnimatedMedusaScene(QWidget):

    def __init__(self):

        super().__init__()

        self.setMinimumHeight(
            220
        )

        self.state = "CALM"

        self.phase = 0.0

        self.blink_counter = 0

        self.blinking = False

        self.bubbles = []

        for _ in range(
            20
        ):

            self.bubbles.append(
                {
                    "x":
                        random.randint(
                            5,
                            500
                        ),

                    "y":
                        random.randint(
                            0,
                            220
                        ),

                    "r":
                        random.uniform(
                            2.0,
                            7.0
                        ),

                    "speed":
                        random.uniform(
                            0.25,
                            0.85
                        ),

                    "drift":
                        random.uniform(
                            0.4,
                            1.2
                        ),
                }
            )

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.animate
        )

        self.timer.start(
            33
        )

    # =================================================

    def set_state(
        self,
        state
    ):

        self.state = state

        self.update()

    # =================================================

    def state_color(self):

        if self.state == "ACTIVE":
            return GREEN

        if self.state == "SUSPICIOUS":
            return PURPLE

        if self.state == "CRITICAL":
            return RED

        return CYAN

    # =================================================

    def animate(self):

        speeds = {
            "CALM":
                0.035,

            "ACTIVE":
                0.055,

            "SUSPICIOUS":
                0.09,

            "CRITICAL":
                0.15,
        }

        self.phase += speeds.get(
            self.state,
            0.035
        )

        # ---------------------------------------------
        # BOLLE
        # ---------------------------------------------

        for bubble in (
            self.bubbles
        ):

            bubble["y"] -= (
                bubble["speed"]
            )

            bubble["x"] += (
                math.sin(
                    self.phase
                    * bubble["drift"]
                )
                * 0.12
            )

            if bubble["y"] < -12:

                bubble["y"] = (
                    self.height()
                    + random.randint(
                        5,
                        35
                    )
                )

                bubble["x"] = (
                    random.randint(
                        5,
                        max(
                            10,
                            self.width()
                            - 5
                        )
                    )
                )

        # ---------------------------------------------
        # BLINK
        # ---------------------------------------------

        self.blink_counter += 1

        if (
            not self.blinking
            and
            self.blink_counter > 110
        ):

            self.blinking = True

            self.blink_counter = 0

        elif (
            self.blinking
            and
            self.blink_counter > 5
        ):

            self.blinking = False

            self.blink_counter = 0

        self.update()

    # =================================================

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        self.draw_ocean(
            painter
        )

        self.draw_bubbles(
            painter
        )

        self.draw_medusa(
            painter
        )

        self.draw_brand(
            painter
        )

        self.draw_badge(
            painter
        )

    # =================================================
    # OCEANO
    # =================================================

    def draw_ocean(
        self,
        painter
    ):

        gradient = QLinearGradient(
            0,
            0,
            0,
            self.height()
        )

        gradient.setColorAt(
            0,
            QColor("#071A23")
        )

        gradient.setColorAt(
            0.55,
            QColor("#06151D")
        )

        gradient.setColorAt(
            1,
            QColor("#051117")
        )

        painter.fillRect(
            self.rect(),
            gradient
        )

        # ---------------------------------------------
        # RAGGI DI LUCE
        # ---------------------------------------------

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                80,
                220,
                245,
                12
            )
        )

        for offset in (
            25,
            145,
            315,
            430
        ):

            path = QPainterPath()

            path.moveTo(
                offset,
                0
            )

            path.lineTo(
                offset + 55,
                0
            )

            path.lineTo(
                offset + 100,
                self.height()
            )

            path.lineTo(
                offset + 15,
                self.height()
            )

            path.closeSubpath()

            painter.drawPath(
                path
            )

        # ---------------------------------------------
        # ONDE
        # ---------------------------------------------

        painter.setPen(
            QPen(
                QColor(
                    42,
                    145,
                    170,
                    55
                ),
                1.2
            )
        )

        for row in range(
            5
        ):

            path = QPainterPath()

            base_y = (
                168
                + row * 10
            )

            path.moveTo(
                0,
                base_y
            )

            for x in range(
                0,
                self.width() + 18,
                18
            ):

                y = (
                    base_y
                    + math.sin(
                        x * 0.032
                        + self.phase
                        + row
                    )
                    * 3
                )

                path.lineTo(
                    x,
                    y
                )

            painter.drawPath(
                path
            )

        # ---------------------------------------------
        # ALGHE
        # ---------------------------------------------

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                20,
                95,
                100,
                55
            )
        )

        positions = (
            15,
            38,
            self.width() - 50,
            self.width() - 28
        )

        for x in positions:

            path = QPainterPath()

            path.moveTo(
                x,
                self.height()
            )

            path.cubicTo(
                x - 8,
                self.height() - 22,

                x + 12,
                self.height() - 34,

                x,
                self.height() - 52
            )

            path.cubicTo(
                x + 18,
                self.height() - 35,

                x - 7,
                self.height() - 16,

                x + 5,
                self.height()
            )

            path.closeSubpath()

            painter.drawPath(
                path
            )

    # =================================================
    # BOLLE
    # =================================================

    def draw_bubbles(
        self,
        painter
    ):

        for bubble in (
            self.bubbles
        ):

            radius = bubble[
                "r"
            ]

            x = bubble[
                "x"
            ]

            y = bubble[
                "y"
            ]

            painter.setPen(
                QPen(
                    QColor(
                        96,
                        226,
                        255,
                        135
                    ),
                    1.2
                )
            )

            painter.setBrush(
                QColor(
                    96,
                    226,
                    255,
                    20
                )
            )

            painter.drawEllipse(
                QPointF(
                    x,
                    y
                ),
                radius,
                radius
            )

            # riflessino
            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                QColor(
                    220,
                    250,
                    255,
                    135
                )
            )

            painter.drawEllipse(
                QPointF(
                    x
                    - radius * 0.35,

                    y
                    - radius * 0.35
                ),
                radius * 0.18,
                radius * 0.18
            )

    # =================================================
    # SINGOLO SERPENTE
    # =================================================

    def draw_snake(
        self,
        painter,
        start,
        control1,
        control2,
        end,
        index,
        color
    ):

        wiggle = (
            math.sin(
                self.phase * 1.2
                + index * 0.75
            )
        )

        path = QPainterPath()

        path.moveTo(
            start[0],
            start[1]
        )

        path.cubicTo(
            control1[0]
            + wiggle * 5,

            control1[1],

            control2[0]
            - wiggle * 5,

            control2[1],

            end[0],
            end[1]
        )

        # contorno cartoon
        painter.setPen(
            QPen(
                INK,
                9,
                Qt.SolidLine,
                Qt.RoundCap
            )
        )

        painter.drawPath(
            path
        )

        painter.setPen(
            QPen(
                color,
                6,
                Qt.SolidLine,
                Qt.RoundCap
            )
        )

        painter.drawPath(
            path
        )

        # ---------------------------------------------
        # TESTINA
        # ---------------------------------------------

        ex = end[0]

        ey = end[1]

        painter.setPen(
            QPen(
                INK,
                2
            )
        )

        painter.setBrush(
            color
        )

        painter.drawEllipse(
            QRectF(
                ex - 7,
                ey - 6,
                14,
                12
            )
        )

        # occhio
        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            YELLOW
        )

        painter.drawEllipse(
            QPointF(
                ex + 2,
                ey - 1
            ),
            2.2,
            2.8
        )

        painter.setBrush(
            INK
        )

        painter.drawEllipse(
            QPointF(
                ex + 2.6,
                ey - 1
            ),
            0.8,
            1.4
        )

        # linguetta
        if index % 2 == 0:

            painter.setPen(
                QPen(
                    QColor("#FF6B8F"),
                    1.5,
                    Qt.SolidLine,
                    Qt.RoundCap
                )
            )

            painter.drawLine(
                QPointF(
                    ex + 7,
                    ey + 1
                ),
                QPointF(
                    ex + 12,
                    ey + 2
                )
            )

    # =================================================
    # MEDUSA
    # =================================================

    def draw_medusa(
        self,
        painter
    ):

        cx = 105

        cy = (
            112
            + math.sin(
                self.phase
            )
            * 2.4
        )

        if self.state == "CRITICAL":

            cx += (
                math.sin(
                    self.phase * 8
                )
                * 2.2
            )

        # ---------------------------------------------
        # COLORE SERPENTI
        # ---------------------------------------------

        snake_color = (
            CYAN_DARK
        )

        if self.state == "SUSPICIOUS":

            snake_color = (
                PURPLE_DARK
            )

        elif self.state == "CRITICAL":

            snake_color = QColor(
                "#CE3D62"
            )

        snakes = [
            (
                (72, 91),
                (48, 60),
                (36, 35),
                (50, 24)
            ),
            (
                (82, 78),
                (70, 38),
                (72, 19),
                (88, 17)
            ),
            (
                (96, 73),
                (90, 35),
                (103, 16),
                (117, 19)
            ),
            (
                (112, 74),
                (122, 34),
                (137, 20),
                (150, 28)
            ),
            (
                (126, 81),
                (147, 46),
                (167, 41),
                (176, 52)
            ),
            (
                (134, 94),
                (167, 73),
                (184, 78),
                (189, 92)
            ),
        ]

        for index, snake in enumerate(
            snakes
        ):

            start, c1, c2, end = snake

            offset_y = (
                cy - 112
            )

            self.draw_snake(
                painter,

                (
                    start[0],
                    start[1] + offset_y
                ),

                (
                    c1[0],
                    c1[1] + offset_y
                ),

                (
                    c2[0],
                    c2[1] + offset_y
                ),

                (
                    end[0],
                    end[1] + offset_y
                ),

                index,

                snake_color
            )

        # ---------------------------------------------
        # MASSA CAPELLI
        # ---------------------------------------------

        painter.setPen(
            QPen(
                INK,
                3
            )
        )

        hair_gradient = (
            QRadialGradient(
                QPointF(
                    cx - 10,
                    cy - 30
                ),
                65
            )
        )

        hair_gradient.setColorAt(
            0,
            QColor("#2BC3DB")
        )

        hair_gradient.setColorAt(
            1,
            QColor("#1184A4")
        )

        painter.setBrush(
            hair_gradient
        )

        painter.drawEllipse(
            QRectF(
                cx - 50,
                cy - 55,
                100,
                88
            )
        )

        # ---------------------------------------------
        # VISO
        # ---------------------------------------------

        face = QPainterPath()

        face.moveTo(
            cx - 35,
            cy - 25
        )

        face.cubicTo(
            cx - 42,
            cy - 1,

            cx - 31,
            cy + 36,

            cx,
            cy + 43
        )

        face.cubicTo(
            cx + 31,
            cy + 36,

            cx + 42,
            cy - 1,

            cx + 35,
            cy - 25
        )

        face.cubicTo(
            cx + 20,
            cy - 42,

            cx - 20,
            cy - 42,

            cx - 35,
            cy - 25
        )

        face.closeSubpath()

        painter.setPen(
            QPen(
                INK,
                3
            )
        )

        face_gradient = (
            QLinearGradient(
                cx,
                cy - 35,
                cx,
                cy + 45
            )
        )

        face_gradient.setColorAt(
            0,
            QColor("#D5F0D8")
        )

        face_gradient.setColorAt(
            1,
            SKIN
        )

        painter.setBrush(
            face_gradient
        )

        painter.drawPath(
            face
        )

        # ---------------------------------------------
        # CONCHIGLIA
        # ---------------------------------------------

        painter.setPen(
            QPen(
                INK,
                2
            )
        )

        painter.setBrush(
            QColor("#F3C36A")
        )

        shell = QPainterPath()

        shell.moveTo(
            cx + 6,
            cy - 40
        )

        shell.cubicTo(
            cx + 11,
            cy - 54,

            cx + 21,
            cy - 54,

            cx + 21,
            cy - 39
        )

        shell.cubicTo(
            cx + 28,
            cy - 52,

            cx + 38,
            cy - 47,

            cx + 31,
            cy - 34
        )

        shell.cubicTo(
            cx + 22,
            cy - 25,

            cx + 11,
            cy - 29,

            cx + 6,
            cy - 40
        )

        shell.closeSubpath()

        painter.drawPath(
            shell
        )

        # ---------------------------------------------
        # GUANCE
        # ---------------------------------------------

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(
            QColor(
                255,
                125,
                150,
                48
            )
        )

        painter.drawEllipse(
            QPointF(
                cx - 24,
                cy + 20
            ),
            7,
            4
        )

        painter.drawEllipse(
            QPointF(
                cx + 24,
                cy + 20
            ),
            7,
            4
        )

        # ---------------------------------------------
        # OCCHI
        # ---------------------------------------------

        eye_height = 23

        if self.blinking:

            eye_height = 3.2

        painter.setPen(
            QPen(
                INK,
                2
            )
        )

        painter.setBrush(
            QColor("#FFFDF5")
        )

        painter.drawEllipse(
            QRectF(
                cx - 29,
                cy - 10,
                21,
                eye_height
            )
        )

        painter.drawEllipse(
            QRectF(
                cx + 8,
                cy - 10,
                21,
                eye_height
            )
        )

        if not self.blinking:

            pupil = 0

            if self.state == "ACTIVE":

                pupil = (
                    math.sin(
                        self.phase * 1.5
                    )
                    * 2.8
                )

            elif self.state in (
                "SUSPICIOUS",
                "CRITICAL"
            ):

                pupil = 1.8

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                INK
            )

            painter.drawEllipse(
                QPointF(
                    cx - 17
                    + pupil,

                    cy + 2
                ),
                3.3,
                5.3
            )

            painter.drawEllipse(
                QPointF(
                    cx + 20
                    + pupil,

                    cy + 2
                ),
                3.3,
                5.3
            )

            # riflesso
            painter.setBrush(
                QColor("#FFFFFF")
            )

            painter.drawEllipse(
                QPointF(
                    cx - 18
                    + pupil,

                    cy
                ),
                0.9,
                1.3
            )

            painter.drawEllipse(
                QPointF(
                    cx + 19
                    + pupil,

                    cy
                ),
                0.9,
                1.3
            )

        # ---------------------------------------------
        # SOPRACCIGLIA
        # ---------------------------------------------

        if self.state in (
            "SUSPICIOUS",
            "CRITICAL"
        ):

            painter.setPen(
                QPen(
                    INK,
                    3,
                    Qt.SolidLine,
                    Qt.RoundCap
                )
            )

            painter.drawLine(
                QPointF(
                    cx - 31,
                    cy - 17
                ),

                QPointF(
                    cx - 10,
                    cy - 10
                )
            )

            painter.drawLine(
                QPointF(
                    cx + 10,
                    cy - 10
                ),

                QPointF(
                    cx + 31,
                    cy - 17
                )
            )

        # ---------------------------------------------
        # BOCCA
        # ---------------------------------------------

        painter.setPen(
            QPen(
                INK,
                3,
                Qt.SolidLine,
                Qt.RoundCap
            )
        )

        if self.state == "CALM":

            painter.drawArc(
                QRectF(
                    cx - 14,
                    cy + 21,
                    28,
                    16
                ),
                200 * 16,
                140 * 16
            )

        elif self.state == "ACTIVE":

            painter.drawArc(
                QRectF(
                    cx - 16,
                    cy + 18,
                    32,
                    20
                ),
                190 * 16,
                160 * 16
            )

        elif self.state == "SUSPICIOUS":

            painter.drawLine(
                QPointF(
                    cx - 13,
                    cy + 30
                ),

                QPointF(
                    cx + 13,
                    cy + 27
                )
            )

        else:

            painter.setBrush(
                INK
            )

            painter.drawEllipse(
                QRectF(
                    cx - 14,
                    cy + 17,
                    28,
                    21
                )
            )

            painter.setPen(
                Qt.NoPen
            )

            painter.setBrush(
                CREAM
            )

            for offset in (
                -7,
                0,
                7
            ):

                tooth = (
                    QPainterPath()
                )

                tooth.moveTo(
                    cx + offset - 3,
                    cy + 18
                )

                tooth.lineTo(
                    cx + offset + 3,
                    cy + 18
                )

                tooth.lineTo(
                    cx + offset,
                    cy + 25
                )

                tooth.closeSubpath()

                painter.drawPath(
                    tooth
                )

        # ---------------------------------------------
        # BRACCIA / SPALLE
        # ---------------------------------------------

        painter.setPen(
            QPen(
                INK,
                3
            )
        )

        painter.setBrush(
            SKIN_SHADOW
        )

        left_arm = QPainterPath()

        left_arm.moveTo(
            cx - 31,
            cy + 35
        )

        left_arm.cubicTo(
            cx - 55,
            cy + 43,

            cx - 58,
            cy + 64,

            cx - 35,
            cy + 61
        )

        left_arm.cubicTo(
            cx - 20,
            cy + 56,

            cx - 14,
            cy + 48,

            cx - 9,
            cy + 41
        )

        left_arm.closeSubpath()

        painter.drawPath(
            left_arm
        )

        right_arm = QPainterPath()

        right_arm.moveTo(
            cx + 31,
            cy + 35
        )

        right_arm.cubicTo(
            cx + 55,
            cy + 43,

            cx + 58,
            cy + 64,

            cx + 35,
            cy + 61
        )

        right_arm.cubicTo(
            cx + 20,
            cy + 56,

            cx + 14,
            cy + 48,

            cx + 9,
            cy + 41
        )

        right_arm.closeSubpath()

        painter.drawPath(
            right_arm
        )

    # =================================================
    # BRAND
    # =================================================

    def draw_brand(
        self,
        painter
    ):

        title_font = QFont(
            "Cooper Black",
            30
        )

        title_font.setBold(
            True
        )

        painter.setFont(
            title_font
        )

        # ombra
        painter.setPen(
            QColor(
                0,
                0,
                0,
                115
            )
        )

        painter.drawText(
            QRectF(
                204,
                43,
                self.width() - 225,
                54
            ),
            Qt.AlignLeft
            | Qt.AlignVCenter,
            "MEDUSA"
        )

        # testo
        painter.setPen(
            CREAM
        )

        painter.drawText(
            QRectF(
                201,
                40,
                self.width() - 225,
                54
            ),
            Qt.AlignLeft
            | Qt.AlignVCenter,
            "MEDUSA"
        )

        subtitle = QFont(
            "Consolas",
            8
        )

        subtitle.setLetterSpacing(
            QFont.AbsoluteSpacing,
            2.1
        )

        painter.setFont(
            subtitle
        )

        painter.setPen(
            QColor("#78A8B5")
        )

        painter.drawText(
            QRectF(
                205,
                88,
                250,
                24
            ),
            Qt.AlignLeft
            | Qt.AlignVCenter,
            "NETWORK OBSERVER"
        )

    # =================================================
    # BADGE
    # =================================================

    def draw_badge(
        self,
        painter
    ):

        color = (
            self.state_color()
        )

        badge = QRectF(
            self.width() - 147,
            124,
            127,
            38
        )

        painter.setPen(
            QPen(
                color,
                1.8
            )
        )

        painter.setBrush(
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                30
            )
        )

        painter.drawRoundedRect(
            badge,
            16,
            16
        )

        painter.setFont(
            QFont(
                "Consolas",
                9,
                QFont.Weight.Bold
            )
        )

        painter.setPen(
            color
        )

        painter.drawText(
            badge,
            Qt.AlignCenter,
            f"● {self.state}"
        )


# =====================================================
# CONNECTION CARD
# =====================================================

class ConnectionCard(QFrame):

    def __init__(
        self,
        connection
    ):

        super().__init__()

        self.setObjectName(
            "connectionCard"
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            12,
            14,
            12
        )

        layout.setSpacing(
            4
        )

        process = QLabel(
            str(
                connection.get(
                    "process",
                    "Sconosciuto"
                )
            )
        )

        process.setObjectName(
            "connectionProcess"
        )

        meta = QLabel(
            f"{connection.get('direction', '—')}"
            f"  •  "
            f"{connection.get('status', '—')}"
        )

        meta.setObjectName(
            "connectionMeta"
        )

        local = QLabel(
            "LOCALE\n"
            + str(
                connection.get(
                    "local",
                    "—"
                )
            )
        )

        local.setObjectName(
            "connectionAddress"
        )

        remote = QLabel(
            "REMOTO\n"
            + str(
                connection.get(
                    "remote",
                    "—"
                )
            )
        )

        remote.setObjectName(
            "connectionAddress"
        )

        pid = QLabel(
            f"PID "
            f"{connection.get('pid', '—')}"
        )

        pid.setObjectName(
            "connectionPid"
        )

        layout.addWidget(
            process
        )

        layout.addWidget(
            meta
        )

        layout.addSpacing(
            4
        )

        layout.addWidget(
            local
        )

        layout.addWidget(
            remote
        )

        layout.addWidget(
            pid
        )


# =====================================================
# DETAILS
# =====================================================

class ConnectionDetailsDialog(
    QDialog
):

    def __init__(
        self,
        service_name,
        port,
        connections,
        recent_events,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.setWindowTitle(
            f"MEDUSA — {service_name}"
        )

        self.resize(
            540,
            650
        )

        self.setObjectName(
            "detailsDialog"
        )

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            24,
            24,
            24,
            24
        )

        root.setSpacing(
            12
        )

        title = QLabel(
            service_name
        )

        title.setObjectName(
            "detailsTitle"
        )

        subtitle = QLabel(
            f"PORTA {port}"
        )

        subtitle.setObjectName(
            "detailsSubtitle"
        )

        count = QLabel(
            f"{len(connections)} ATTIVE ORA"
            f"   •   "
            f"{len(recent_events)} NUOVE / 60s"
        )

        count.setObjectName(
            "detailsCount"
        )

        root.addWidget(
            title
        )

        root.addWidget(
            subtitle
        )

        root.addWidget(
            count
        )

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.NoFrame
        )

        content = QWidget()

        content_layout = (
            QVBoxLayout(
                content
            )
        )

        content_layout.setSpacing(
            10
        )

        content_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        if not connections:

            empty = QLabel(
                "Nessuna connessione "
                "attiva in questo momento."
            )

            empty.setObjectName(
                "detailsEmpty"
            )

            empty.setAlignment(
                Qt.AlignCenter
            )

            content_layout.addWidget(
                empty
            )

        else:

            for connection in (
                connections
            ):

                content_layout.addWidget(
                    ConnectionCard(
                        connection
                    )
                )

        content_layout.addStretch()

        scroll.setWidget(
            content
        )

        root.addWidget(
            scroll
        )

        close_button = QPushButton(
            "CHIUDI"
        )

        close_button.setObjectName(
            "detailsCloseButton"
        )

        close_button.clicked.connect(
            self.close
        )

        root.addWidget(
            close_button
        )


# =====================================================
# PORT ROW
# =====================================================

class PortRow(QFrame):

    clicked = Signal(
        str,
        int,
        list,
        list
    )

    def __init__(
        self,
        name,
        port
    ):

        super().__init__()

        self.name = name

        self.port = port

        self.connections = []

        self.recent_events = []

        self.setObjectName(
            "portRow"
        )

        self.setCursor(
            QCursor(
                Qt.PointingHandCursor
            )
        )

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            12,
            8,
            12,
            8
        )

        root.setSpacing(
            4
        )

        top = QHBoxLayout()

        top.setSpacing(
            8
        )

        self.icon = ServiceIcon(
            name
        )

        self.service_label = QLabel(
            name
        )

        self.service_label.setObjectName(
            "serviceName"
        )

        self.port_label = QLabel(
            str(port)
        )

        self.port_label.setObjectName(
            "portNumber"
        )

        self.status_label = QLabel(
            "● OFF"
        )

        self.status_label.setObjectName(
            "statusClosed"
        )

        self.status_label.setAlignment(
            Qt.AlignCenter
        )

        self.tentacle = (
            TentacleIndicator()
        )

        self.arrow = QLabel(
            "›"
        )

        self.arrow.setObjectName(
            "rowArrow"
        )

        self.arrow.setAlignment(
            Qt.AlignCenter
        )

        top.addWidget(
            self.icon
        )

        top.addWidget(
            self.service_label
        )

        top.addWidget(
            self.port_label
        )

        top.addStretch()

        top.addWidget(
            self.status_label
        )

        top.addWidget(
            self.tentacle
        )

        top.addWidget(
            self.arrow
        )

        self.connection_detail = QLabel(
            ""
        )

        self.connection_detail.setObjectName(
            "connectionDetail"
        )

        self.connection_detail.setAlignment(
            Qt.AlignRight
        )

        self.connection_detail.hide()

        root.addLayout(
            top
        )

        root.addWidget(
            self.connection_detail
        )

    # =================================================

    def mousePressEvent(
        self,
        event
    ):

        if (
            event.button()
            == Qt.LeftButton
        ):

            self.clicked.emit(
                self.name,
                self.port,
                self.connections,
                self.recent_events
            )

        super().mousePressEvent(
            event
        )

    # =================================================

    def set_status(
        self,
        status,
        reason="",
        process_name=None,
        local_address=None,
        remote_address=None,
        connections=None,
        recent_events=None
    ):

        self.connections = (
            connections or []
        )

        self.recent_events = (
            recent_events or []
        )

        self.icon.set_status(
            status
        )

        self.tentacle.set_status(
            status
        )

        if status == "ACTIVE":

            self.status_label.setText(
                "● ATTIVA"
            )

            self.status_label.setObjectName(
                "statusActive"
            )

        elif status == "LISTENING":

            self.status_label.setText(
                "● ASCOLTO"
            )

            self.status_label.setObjectName(
                "statusWarning"
            )

        elif status == "SERVER_OFF":

            self.status_label.setText(
                "● SERVER OFF"
            )

            self.status_label.setObjectName(
                "statusDisabled"
            )

        else:

            self.status_label.setText(
                "● OFF"
            )

            self.status_label.setObjectName(
                "statusClosed"
            )

        count = len(
            self.connections
        )

        if (
            status == "ACTIVE"
            and process_name
            and remote_address
            and remote_address != "—"
        ):

            text = (
                f"{process_name}"
                f"  →  "
                f"{remote_address}"
            )

            if count > 1:

                text += (
                    f"   +{count - 1}"
                )

            self.connection_detail.setText(
                text
            )

            self.connection_detail.show()

        elif (
            status == "LISTENING"
            and process_name
        ):

            self.connection_detail.setText(
                f"{process_name}"
                f"  •  "
                f"{local_address}"
            )

            self.connection_detail.show()

        else:

            self.connection_detail.hide()

        self.setToolTip(
            f"{reason}\n\n"
            f"Attive ora: {count}\n"
            f"Nuove ultimi 60s: "
            f"{len(self.recent_events)}"
        )

        self.status_label.style().unpolish(
            self.status_label
        )

        self.status_label.style().polish(
            self.status_label
        )


# =====================================================
# MAIN
# =====================================================

class MedusaWidget(QWidget):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "MEDUSA"
        )

        self.setFixedSize(
            540,
            840
        )

        self.current_download = 0

        self.current_upload = 0

        self.details_dialog = None

        self.build_ui()

        # ---------------------------------------------
        # TRAFFIC
        # ---------------------------------------------

        self.traffic_timer = QTimer(
            self
        )

        self.traffic_timer.timeout.connect(
            self.update_traffic
        )

        self.traffic_timer.start(
            500
        )

        get_network_speed()

        # ---------------------------------------------
        # WORKER
        # ---------------------------------------------

        self.network_worker = (
            NetworkWorker(
                interval=1.5,
                parent=self
            )
        )

        self.network_worker.snapshot_ready.connect(
            self.apply_network_snapshot
        )

        self.network_worker.scan_error.connect(
            self.handle_network_error
        )

        self.network_worker.start()

    # =================================================

    def build_ui(self):

        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            18,
            16,
            18,
            16
        )

        root.setSpacing(
            10
        )

        # ---------------------------------------------
        # HEADER
        # ---------------------------------------------

        self.medusa_scene = (
            AnimatedMedusaScene()
        )

        root.addWidget(
            self.medusa_scene
        )

        # ---------------------------------------------
        # PC
        # ---------------------------------------------

        pc_card = QFrame()

        pc_card.setObjectName(
            "mainCard"
        )

        pc_layout = QHBoxLayout(
            pc_card
        )

        pc_layout.setContentsMargins(
            16,
            11,
            16,
            11
        )

        left = QVBoxLayout()

        left.setSpacing(
            1
        )

        pc_title = QLabel(
            "QUESTO PC"
        )

        pc_title.setObjectName(
            "smallLabel"
        )

        pc_name = QLabel(
            "Sistema monitorato"
        )

        pc_name.setObjectName(
            "protectedText"
        )

        left.addWidget(
            pc_title
        )

        left.addWidget(
            pc_name
        )

        pc_layout.addLayout(
            left
        )

        pc_layout.addStretch()

        online = QLabel(
            "● ONLINE"
        )

        online.setObjectName(
            "liveStatus"
        )

        pc_layout.addWidget(
            online
        )

        root.addWidget(
            pc_card
        )

        # ---------------------------------------------
        # PORTS
        # ---------------------------------------------

        section = QLabel(
            "PORTE MONITORATE"
        )

        section.setObjectName(
            "sectionTitle"
        )

        root.addWidget(
            section
        )

        self.port_rows = {

            "HTTPS":
                PortRow(
                    "HTTPS",
                    443
                ),

            "DNS":
                PortRow(
                    "DNS",
                    53
                ),

            "SMB":
                PortRow(
                    "SMB",
                    445
                ),

            "RDP":
                PortRow(
                    "RDP",
                    3389
                ),

            "SSH":
                PortRow(
                    "SSH",
                    22
                ),
        }

        for row in (
            self.port_rows.values()
        ):

            row.clicked.connect(
                self.open_port_details
            )

            root.addWidget(
                row
            )

        # ---------------------------------------------
        # STATS
        # ---------------------------------------------

        stats = QHBoxLayout()

        stats.setSpacing(
            10
        )

        # TRAFFIC

        traffic_card = QFrame()

        traffic_card.setObjectName(
            "statCard"
        )

        traffic_layout = QVBoxLayout(
            traffic_card
        )

        traffic_layout.setContentsMargins(
            14,
            11,
            14,
            11
        )

        traffic_layout.setSpacing(
            4
        )

        traffic_title = QLabel(
            "≈  TRAFFICO LIVE"
        )

        traffic_title.setObjectName(
            "statTitle"
        )

        values = QHBoxLayout()

        self.download_value = QLabel(
            "↓ 0 B/s"
        )

        self.download_value.setObjectName(
            "downloadValue"
        )

        self.upload_value = QLabel(
            "↑ 0 B/s"
        )

        self.upload_value.setObjectName(
            "uploadValue"
        )

        values.addWidget(
            self.download_value
        )

        values.addStretch()

        values.addWidget(
            self.upload_value
        )

        self.traffic_bars = (
            TrafficBars()
        )

        traffic_layout.addWidget(
            traffic_title
        )

        traffic_layout.addLayout(
            values
        )

        traffic_layout.addWidget(
            self.traffic_bars
        )

        # CONNECTIONS

        connection_card = QFrame()

        connection_card.setObjectName(
            "statCard"
        )

        connection_layout = (
            QVBoxLayout(
                connection_card
            )
        )

        connection_layout.setContentsMargins(
            14,
            11,
            14,
            11
        )

        connection_layout.setSpacing(
            3
        )

        connection_title = QLabel(
            "⌁  CONNESSIONI"
        )

        connection_title.setObjectName(
            "statTitle"
        )

        self.connection_value = QLabel(
            "0"
        )

        self.connection_value.setObjectName(
            "bigConnectionValue"
        )

        self.recent_value = QLabel(
            "0 nuove / 60s"
        )

        self.recent_value.setObjectName(
            "recentValue"
        )

        connection_layout.addWidget(
            connection_title
        )

        connection_layout.addWidget(
            self.connection_value
        )

        connection_layout.addWidget(
            self.recent_value
        )

        connection_layout.addStretch()

        stats.addWidget(
            traffic_card,
            3
        )

        stats.addWidget(
            connection_card,
            2
        )

        root.addLayout(
            stats
        )

        # ---------------------------------------------
        # FOOTER
        # ---------------------------------------------

        footer = QFrame()

        footer.setObjectName(
            "monitoringFooter"
        )

        footer_layout = QHBoxLayout(
            footer
        )

        footer_layout.setContentsMargins(
            14,
            7,
            14,
            7
        )

        self.monitoring_status = QLabel(
            "✦ MONITORAGGIO ATTIVO"
        )

        self.monitoring_status.setObjectName(
            "protectedStatus"
        )

        version = QLabel(
            "MEDUSA 0.5.0"
        )

        version.setObjectName(
            "versionText"
        )

        footer_layout.addWidget(
            self.monitoring_status
        )

        footer_layout.addStretch()

        footer_layout.addWidget(
            version
        )

        root.addWidget(
            footer
        )

    # =================================================
    # STATE
    # =================================================

    def calculate_medusa_state(
        self,
        connections,
        recent
    ):

        # Per ora controllano solo
        # l'animazione visiva.

        if recent >= 90:
            return "CRITICAL"

        if recent >= 40:
            return "SUSPICIOUS"

        traffic = (
            self.current_download
            + self.current_upload
        )

        if (
            connections >= 5
            or recent >= 8
            or traffic >= 250 * 1024
        ):

            return "ACTIVE"

        return "CALM"

    # =================================================

    def open_port_details(
        self,
        service_name,
        port,
        connections,
        recent_events
    ):

        self.details_dialog = (
            ConnectionDetailsDialog(
                service_name,
                port,
                connections,
                recent_events,
                self
            )
        )

        self.details_dialog.show()

    # =================================================

    def update_traffic(self):

        try:

            speed = (
                get_network_speed()
            )

            self.current_download = (
                speed[
                    "download_bps"
                ]
            )

            self.current_upload = (
                speed[
                    "upload_bps"
                ]
            )

            self.download_value.setText(
                "↓ "
                + format_speed(
                    self.current_download
                )
            )

            self.upload_value.setText(
                "↑ "
                + format_speed(
                    self.current_upload
                )
            )

            self.traffic_bars.add_sample(
                self.current_download,
                self.current_upload
            )

        except Exception as error:

            print(
                "Errore traffico MEDUSA:",
                error
            )

    # =================================================

    def apply_network_snapshot(
        self,
        data
    ):

        for (
            name,
            info
        ) in data[
            "ports"
        ].items():

            self.port_rows[
                name
            ].set_status(

                status=
                    info["status"],

                reason=
                    info.get(
                        "reason",
                        ""
                    ),

                process_name=
                    info.get(
                        "process_name"
                    ),

                local_address=
                    info.get(
                        "local_address"
                    ),

                remote_address=
                    info.get(
                        "remote_address"
                    ),

                connections=
                    info.get(
                        "connections",
                        []
                    ),

                recent_events=
                    info.get(
                        "recent_events",
                        []
                    ),
            )

        connections = (
            data.get(
                "connections",
                0
            )
        )

        recent = (
            data.get(
                "recent_connection_count",
                0
            )
        )

        self.connection_value.setText(
            str(
                connections
            )
        )

        self.recent_value.setText(
            f"{recent} nuove / 60s"
        )

        state = (
            self.calculate_medusa_state(
                connections,
                recent
            )
        )

        self.medusa_scene.set_state(
            state
        )

        labels = {

            "CALM":
                "✦ RETE TRANQUILLA",

            "ACTIVE":
                "✦ ATTIVITÀ DI RETE",

            "SUSPICIOUS":
                "✦ ATTIVITÀ INSOLITA",

            "CRITICAL":
                "⚠ ATTIVITÀ ELEVATA",
        }

        self.monitoring_status.setText(
            labels[
                state
            ]
        )

        self.monitoring_status.setProperty(
            "state",
            state.lower()
        )

        self.monitoring_status.style().unpolish(
            self.monitoring_status
        )

        self.monitoring_status.style().polish(
            self.monitoring_status
        )

    # =================================================

    def handle_network_error(
        self,
        error
    ):

        print(
            "Errore rete MEDUSA:",
            error
        )

    # =================================================

    def closeEvent(
        self,
        event
    ):

        if (
            hasattr(
                self,
                "network_worker"
            )
            and
            self.network_worker.isRunning()
        ):

            self.network_worker.stop()

            self.network_worker.wait(
                2500
            )

        event.accept()