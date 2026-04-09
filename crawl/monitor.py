from __future__ import annotations

from collections import deque
from contextlib import AbstractContextManager
from datetime import datetime

try:
    from rich.console import Group
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table
except Exception:  # pragma: no cover
    Group = None
    Live = None
    Panel = None
    Table = None


class CrawlMonitor(AbstractContextManager):
    def __init__(self) -> None:
        self.enabled = all(item is not None for item in [Group, Live, Panel, Table])
        self.stage = "Khởi tạo"
        self.detail = ""
        self.current_facility = "-"
        self.current_specialty = "-"
        self.current_doctor = "-"
        self.current_date = "-"
        self.request_count = 0
        self.facility_count = 0
        self.specialty_count = 0
        self.doctor_count = 0
        self.slot_count = 0
        self.events: deque[str] = deque(maxlen=10)
        self.live = None

    def __enter__(self):
        if self.enabled:
            self.live = Live(self._render(), refresh_per_second=8, transient=False)
            self.live.start()
        else:
            print("Bắt đầu crawl dữ liệu từ Vinmec...")
        self.log("Khởi động crawler")
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc:
            self.stage = "Lỗi"
            self.detail = str(exc)
            self.log(f"Lỗi: {exc}")
            self.refresh()
        if self.enabled and self.live:
            self.live.stop()
        return False

    def update_stage(self, stage: str, detail: str = "") -> None:
        self.stage = stage
        self.detail = detail
        self.refresh()

    def set_context(
        self,
        facility: str | None = None,
        specialty: str | None = None,
        doctor: str | None = None,
        date_value: str | None = None,
    ) -> None:
        if facility is not None:
            self.current_facility = facility
        if specialty is not None:
            self.current_specialty = specialty
        if doctor is not None:
            self.current_doctor = doctor
        if date_value is not None:
            self.current_date = date_value
        self.refresh()

    def increment_requests(self, amount: int = 1) -> None:
        self.request_count += amount
        self.refresh()

    def set_counts(
        self,
        facility_count: int | None = None,
        specialty_count: int | None = None,
        doctor_count: int | None = None,
        slot_count: int | None = None,
    ) -> None:
        if facility_count is not None:
            self.facility_count = facility_count
        if specialty_count is not None:
            self.specialty_count = specialty_count
        if doctor_count is not None:
            self.doctor_count = doctor_count
        if slot_count is not None:
            self.slot_count = slot_count
        self.refresh()

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events.appendleft(f"[{timestamp}] {message}")
        self.refresh()
        if not self.enabled:
            print(message)

    def success(self, message: str) -> None:
        self.stage = "Hoàn tất"
        self.detail = message
        self.log(message)
        self.refresh()

    def warning(self, message: str) -> None:
        self.log(f"Cảnh báo: {message}")
        self.refresh()

    def refresh(self) -> None:
        if self.enabled and self.live:
            self.live.update(self._render())

    def _render(self):
        status_table = Table.grid(padding=(0, 1))
        status_table.add_column(style="cyan", justify="right")
        status_table.add_column(style="white")
        status_table.add_row("Giai đoạn", self.stage)
        status_table.add_row("Chi tiết", self.detail or "-")
        status_table.add_row("Cơ sở", self.current_facility)
        status_table.add_row("Chuyên khoa", self.current_specialty)
        status_table.add_row("Bác sĩ", self.current_doctor)
        status_table.add_row("Ngày slot", self.current_date)
        status_table.add_row("Số request", str(self.request_count))

        count_table = Table(title="Số lượng đã thu thập", expand=True)
        count_table.add_column("Cơ sở", justify="center")
        count_table.add_column("Chuyên khoa", justify="center")
        count_table.add_column("Bác sĩ", justify="center")
        count_table.add_column("Slot", justify="center")
        count_table.add_row(
            str(self.facility_count),
            str(self.specialty_count),
            str(self.doctor_count),
            str(self.slot_count),
        )

        event_table = Table.grid()
        event_table.add_column()
        for event in self.events:
            event_table.add_row(event)

        return Group(
            Panel(status_table, title="Vinmec Crawl Monitor", border_style="blue"),
            Panel(count_table, border_style="green"),
            Panel(event_table, title="Nhật ký gần nhất", border_style="magenta"),
        )
