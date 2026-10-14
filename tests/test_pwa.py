"""Browser checks for the local-first reader-to-project journey.

Requires the Python Playwright package and its Chromium browser.
Run: python -m unittest discover -s tests -v
"""

import functools
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
STATE_KEY = "universo-rebeldia-state-v1"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


class JourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT))
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.context = self.browser.new_context(
            viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True
        )
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.context.close()
        self.assertEqual([], self.errors, "Uncaught browser errors")

    def open(self, route="", published=False):
        path = "/docs/app/" if published else "/app/"
        self.page.goto(f"{self.origin}{path}{route}")

    def complete_connections(self):
        self.open("#/livro?c=01_cascavel_z80")
        self.page.locator("#start-reflection").click()
        expect(self.page.locator("#reflection")).to_be_visible()
        self.page.locator("#reflection").fill(
            "Um controlador pode monitorar a temperatura da minha bancada."
        )
        self.page.reload()
        expect(self.page.locator("#reflection")).to_have_value(
            "Um controlador pode monitorar a temperatura da minha bancada."
        )
        self.page.get_by_role("button", name="Salvar e conectar conceitos").click()
        options = self.page.locator('[name="conceptIds"]')
        options.nth(0).check()
        self.page.locator("#connection").fill("Combinar processamento e memória para registrar medições.")
        self.page.get_by_role("button", name="Salvar e criar projeto").click()
        expect(self.page.locator("#connection-status")).to_contain_text("pelo menos dois")
        options.nth(1).check()
        self.page.reload()
        expect(self.page.locator('[name="conceptIds"]:checked')).to_have_count(2)
        expect(self.page.locator("#connection")).to_have_value(
            "Combinar processamento e memória para registrar medições."
        )
        self.page.get_by_role("button", name="Salvar e criar projeto").click()
        expect(self.page.locator("#project-form")).to_be_visible()

    def test_mobile_journey_persistence_offline_and_backup(self):
        self.complete_connections()
        self.page.locator("#project-name").fill("Monitor de bancada")
        self.page.locator("#project-components").fill("Controlador, memória e sensor")
        self.page.reload()
        expect(self.page.locator("#project-name")).to_have_value("Monitor de bancada")
        self.page.get_by_role("button", name="Criar projeto", exact=True).click()
        expect(self.page.locator("#lab-project-count")).to_have_text("0")
        self.page.locator("#project-test").fill("Simular dez leituras e conferir o registro.")
        self.page.locator("#project-result").fill("Registrar as dez leituras sem perda.")
        self.page.get_by_role("button", name="Criar projeto", exact=True).click()
        expect(self.page.locator("#lab-project-count")).to_have_text("1")
        expect(self.page.locator("#project-form h2")).to_have_text("Monitor de bancada")
        project = self.page.evaluate("async () => (await UniverseDB.getProjects())[0]")
        self.assertEqual("01_cascavel_z80", project["chapterId"])
        self.assertEqual(2, len(project["conceptIds"]))
        self.assertIn("temperatura", project["reflection"])
        self.assertIn("memória", project["connection"])
        self.assertIn("dez leituras", project["firstTest"])
        self.page.locator("#project-test").fill("")
        self.page.get_by_role("button", name="Salvar alterações").click()
        self.assertEqual("Simular dez leituras e conferir o registro.", self.page.evaluate(
            "async () => (await UniverseDB.getProjects())[0].firstTest"
        ))
        self.page.locator("#project-test").fill("Simular dez leituras e conferir o registro.")
        self.page.locator("#project-name").fill("Monitor revisado")
        self.page.get_by_role("button", name="Salvar alterações").click()
        expect(self.page.locator("#toast")).to_have_text("Projeto atualizado.")
        self.page.reload()
        expect(self.page.locator("#project-name")).to_have_value("Monitor revisado")
        expect(self.page.locator("#offline-status")).to_have_text(
            "Pronto para usar offline", timeout=20000
        )
        self.context.set_offline(True)
        self.page.reload()
        expect(self.page.locator("#project-name")).to_have_value("Monitor revisado")
        expect(self.page.locator("#offline-status")).to_contain_text("Offline · conteúdo")
        self.page.evaluate("location.hash = '/livro?c=02_anatomia_z80'")
        expect(self.page.locator("#chapter-body")).to_contain_text("Z80")
        self.assertTrue(self.page.evaluate(
            "() => document.documentElement.scrollWidth <= innerWidth"
        ), "Reader must not overflow on mobile, including code blocks")
        self.page.locator("#start-reflection").click()
        self.page.locator("#reflection").fill("Uma reflexão diferente para outro capítulo.")
        self.page.reload()
        expect(self.page.locator("#reflection")).to_have_value(
            "Uma reflexão diferente para outro capítulo."
        )
        self.page.evaluate("location.hash = '/refletir?c=01_cascavel_z80'")
        expect(self.page.locator("#reflection")).to_contain_text("temperatura")
        self.page.evaluate("location.hash = '/configuracoes'")
        with self.page.expect_download() as download_info:
            self.page.locator("#export-data").click()
        backup = json.loads(Path(download_info.value.path()).read_text(encoding="utf-8"))
        self.assertEqual(1, len(backup["projects"]))
        self.assertEqual(2, len(backup["state"]["journeys"]))
        self.page.evaluate(f"""async () => {{
          await UniverseDB.clearProjects();
          const state = JSON.parse(localStorage.getItem('{STATE_KEY}'));
          state.journeys = {{}};
          localStorage.setItem('{STATE_KEY}', JSON.stringify(state));
        }}""")
        with self.page.expect_navigation():
            self.page.locator("#import-data").set_input_files({
                "name": "backup.json",
                "mimeType": "application/json",
                "buffer": json.dumps(backup).encode(),
            })
        expect(self.page.locator("#export-data")).to_be_visible()
        self.page.evaluate("location.hash = '/laboratorio'")
        expect(self.page.locator("#lab-project-count")).to_have_text("1")
        self.page.get_by_role("button", name="Monitor revisado").click()
        expect(self.page.locator("#project-test")).to_have_value(
            "Simular dez leituras e conferir o registro."
        )
        self.page.on("dialog", lambda dialog: dialog.accept())
        self.page.locator("#delete-project").click()
        expect(self.page.locator("#lab-project-count")).to_have_text("0")
        self.assertEqual(
            "", self.page.evaluate(
                f"JSON.parse(localStorage.getItem('{STATE_KEY}')).journeys['01_cascavel_z80'].projectId"
            )
        )

    def test_gates_whitespace_legacy_data_and_mobile_layout(self):
        self.open("#/conectar")
        expect(self.page.get_by_role("heading", name="Comece por uma leitura")).to_be_visible()
        self.open("#/conectar?c=01_cascavel_z80")
        expect(self.page.get_by_role("heading", name="Antes, registre sua reflexão")).to_be_visible()
        self.open("#/laboratorio")
        self.page.locator("#new-project").click()
        expect(self.page.get_by_role("heading", name="Comece por uma leitura")).to_be_visible()
        self.open("#/refletir?c=01_cascavel_z80")
        self.page.locator("#reflection").fill("   ")
        self.page.get_by_role("button", name="Salvar e conectar conceitos").click()
        expect(self.page.locator("#reflection")).to_be_visible()
        self.page.locator("#reflection").fill("Uma ideia válida.")
        self.page.get_by_role("button", name="Salvar e conectar conceitos").click()
        for width in (320, 390, 768, 1280):
            self.page.set_viewport_size({"width": width, "height": 844})
            self.assertTrue(self.page.evaluate(
                "() => document.documentElement.scrollWidth <= innerWidth"
            ), f"Horizontal overflow at {width}px")
        self.page.locator('[name="conceptIds"]').nth(0).check()
        self.page.locator("#concept-filter").fill("termo inexistente")
        expect(self.page.locator(".concept-option:visible")).to_have_count(0)
        expect(self.page.locator('[name="conceptIds"]:checked')).to_have_count(1)
        self.page.evaluate("""async () => {
          await UniverseDB.saveProject({ id: 'legacy', name: 'Projeto anterior',
            problem: 'Problema antigo', solution: 'Solução antiga', missionId: 'missao-antiga' });
        }""")
        self.open("#/laboratorio?p=legacy")
        expect(self.page.locator("#project-name")).to_have_value("Projeto anterior")
        self.page.get_by_role("button", name="Salvar alterações").click()
        expect(self.page.locator("#toast")).to_have_text("Projeto atualizado.")
        self.assertEqual("missao-antiga", self.page.evaluate(
            "async () => (await UniverseDB.getProject('legacy')).missionId"
        ))
        self.open("#/desafios")
        expect(self.page.locator("#journey-resume")).to_be_visible()
        expect(self.page.locator('.primary-nav a[href="#/desafios"]')).to_have_count(0)

    def test_storage_failures_are_explicit(self):
        self.open("#/refletir?c=01_cascavel_z80")
        self.page.evaluate("""() => {
          Storage.prototype.setItem = () => { throw new DOMException('Quota exceeded', 'QuotaExceededError'); };
        }""")
        self.page.locator("#reflection").fill("Uma reflexão que não cabe no armazenamento.")
        expect(self.page.locator("#reflection-status")).to_contain_text("Não foi possível salvar")
        self.page.get_by_role("button", name="Salvar e conectar conceitos").click()
        expect(self.page.locator("#reflection")).to_be_visible()
        self.page.reload()
        self.page.evaluate("""() => {
          UniverseDB.getProjects = async () => { throw new Error('Storage unavailable'); };
          location.hash = '/laboratorio';
        }""")
        expect(self.page.get_by_role("heading", name="Banco local indisponível")).to_be_visible()

    def test_full_project_creation_without_network(self):
        self.open()
        expect(self.page.locator("#offline-status")).to_have_text(
            "Pronto para usar offline", timeout=20000
        )
        self.context.set_offline(True)
        self.complete_connections()
        self.page.locator("#project-name").fill("Criado sem rede")
        self.page.locator("#project-test").fill("Simular uma leitura.")
        self.page.locator("#project-result").fill("Uma leitura registrada.")
        self.page.get_by_role("button", name="Criar projeto", exact=True).click()
        expect(self.page.locator("#lab-project-count")).to_have_text("1")
        self.page.reload()
        expect(self.page.locator("#project-name")).to_have_value("Criado sem rede")

    def test_all_chapters_fit_small_mobile_screen(self):
        self.page.set_viewport_size({"width": 320, "height": 740})
        chapters = json.loads((ROOT / "app" / "data" / "capitulos.json").read_text(encoding="utf-8"))
        for chapter in chapters:
            self.open(f"#/livro?c={chapter['id']}")
            expect(self.page.locator("#start-reflection")).to_have_attribute(
                "href", f"#/refletir?c={chapter['id']}"
            )
            self.assertTrue(self.page.evaluate(
                "() => document.documentElement.scrollWidth <= innerWidth"
            ), f"Horizontal overflow in {chapter['id']} at 320px")

    def test_offline_cache_is_scoped_and_published_copy_works(self):
        self.open()
        expect(self.page.locator("#offline-status")).to_have_text(
            "Pronto para usar offline", timeout=20000
        )
        self.open(published=True)
        expect(self.page.locator("#offline-status")).to_have_text(
            "Pronto para usar offline", timeout=20000
        )
        names = self.page.evaluate("() => caches.keys()")
        self.assertTrue(any("/app/:v7" in name and "/docs/" not in name for name in names))
        self.assertTrue(any("/docs/app/:v7" in name for name in names))
        self.context.set_offline(True)
        self.open("#/livro?c=01_cascavel_z80", published=True)
        expect(self.page.locator("#chapter-body")).to_contain_text("Z80")
        self.open("#/livro?c=02_anatomia_z80")
        expect(self.page.locator("#chapter-body")).to_contain_text("Z80")
        response = self.page.goto(f"{self.origin}/app/index.html?source=installed#/dashboard")
        self.assertEqual(200, response.status)
        expect(self.page.locator("#journey-resume")).to_be_visible()


if __name__ == "__main__":
    unittest.main()
