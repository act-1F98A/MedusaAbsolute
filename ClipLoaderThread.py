import base64
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtCore import QThread, Signal
from TwitchAPI import fetch_clips_page, IntegrityError

logger = logging.getLogger(__name__)

PAGE_SIZE = 20
MAX_WORKERS = 6


class ClipLoaderThread(QThread):
    clip_ready = Signal(dict)
    finished_loading = Signal()
    error_occurred = Signal(str)
    progress = Signal(int)

    def __init__(self, channel_name):
        super().__init__()
        self.channel_name = channel_name
        self._stopped = False

    def stop(self):
        self._stopped = True

    def _fetch_page(self, cursor):
        """Fetch a single page. Returns (page_index, clips) or raises."""
        return fetch_clips_page(
            self.channel_name,
            cursor=cursor,
            limit=PAGE_SIZE,
        )

    @staticmethod
    def _make_cursor(offset):
        return base64.b64encode(str(offset).encode()).decode()

    def run(self):
        t_start = time.perf_counter()
        try:
            # 1. Первая страница — проверяем канал
            logger.info("Загрузка клипов для '%s'...", self.channel_name)
            first_clips, first_cursor = self._fetch_page(None)
            logger.info("Первая страница: %d клипов, cursor=%s", len(first_clips), first_cursor)
            if not first_clips or self._stopped:
                if not first_clips:
                    self.error_occurred.emit("Клипы не найдены")
                return

            all_clips = list(first_clips)
            self.progress.emit(len(all_clips))

            if first_cursor and len(first_clips) == PAGE_SIZE:
                # 2. Параллельная загрузка батчами по MAX_WORKERS
                offset = PAGE_SIZE
                done = False
                batch_num = 0

                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                    while not done and not self._stopped:
                        batch_num += 1
                        # Генерируем курсоры для следующего батча
                        batch_cursors = []
                        for _ in range(MAX_WORKERS):
                            batch_cursors.append((offset, self._make_cursor(offset)))
                            offset += PAGE_SIZE

                        offsets_str = ', '.join(str(o) for o, _ in batch_cursors)
                        logger.info("Батч #%d: offsets [%s]", batch_num, offsets_str)
                        t_batch = time.perf_counter()

                        # Запускаем батч параллельно
                        futures = {}
                        for off, cur in batch_cursors:
                            f = pool.submit(self._fetch_page, cur)
                            futures[f] = off

                        # Собираем результаты
                        batch_results = {}
                        for future in as_completed(futures):
                            if self._stopped:
                                done = True
                                break
                            off = futures[future]
                            try:
                                clips, _ = future.result()
                                batch_results[off] = clips
                                logger.debug("  offset=%d: %d клипов", off, len(clips))
                            except IntegrityError:
                                logger.warning("  offset=%d: IntegrityError!", off)
                                done = True
                                break
                            except Exception as e:
                                logger.error("  offset=%d: ошибка %s", off, e)
                                batch_results[off] = []

                        batch_time = time.perf_counter() - t_batch
                        logger.info("Батч #%d завершён за %.2fс", batch_num, batch_time)

                        # Добавляем в порядке offset
                        for off in sorted(batch_results.keys()):
                            clips = batch_results[off]
                            if not clips:
                                logger.debug("  offset=%d пустой — стоп", off)
                                done = True
                                break
                            all_clips.extend(clips)
                            self.progress.emit(len(all_clips))
                            if len(clips) < PAGE_SIZE:
                                logger.debug("  offset=%d неполный (%d) — стоп", off, len(clips))
                                done = True
                                break

            if self._stopped:
                logger.info("Остановлен")
                return

            # 3. Сортировка по дате и emit
            total_time = time.perf_counter() - t_start
            logger.info("Всего: %d клипов за %.2fс, сортировка...", len(all_clips), total_time)
            all_clips.sort(key=lambda c: c.get("timestamp") or 0, reverse=True)

            for clip in all_clips:
                if self._stopped:
                    break
                self.clip_ready.emit(clip)

            logger.info("Готово! %d клипов отправлено в UI", len(all_clips))

        except Exception as e:
            logger.error("ОШИБКА: %s", e, exc_info=True)
            if not self._stopped:
                self.error_occurred.emit(str(e))
        finally:
            self.finished_loading.emit()
