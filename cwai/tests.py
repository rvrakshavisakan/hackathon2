from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from .models import Evaluation
from .views import _calculate_rows
from .guidance import retrieve_evaluation_guidance


class EmissionCalculationTests(TestCase):
    def test_direct_emissions_are_converted_and_aggregated_by_scope(self):
        totals, rows, issues = _calculate_rows([
            {"Activity": "Electricity", "CO2e Emissions": 420.5, "Scope": "2"},
            {"Activity": "Company Vehicles", "Emissions": 185.2, "Scope": "1"},
        ])
        self.assertAlmostEqual(totals["scope2"], 0.4205)
        self.assertAlmostEqual(totals["scope1"], 0.1852)
        self.assertAlmostEqual(sum(totals.values()), 0.6057)
        self.assertEqual(len(rows), 2)
        self.assertEqual(issues, [])

    def test_quantity_times_factor_and_validation(self):
        totals, rows, issues = _calculate_rows([
            {"Activity": "Purchased goods", "Quantity": 2, "Unit": "kg", "Emission factor": 1.5},
            {"Activity": "Unknown", "Quantity": -1, "Emission factor": 4},
        ])
        self.assertEqual(totals["scope3"], 0.003)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(issues), 1)

    def test_evaluation_records_are_user_scoped(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(username="analyst", password="a-long-test-password")
        evaluation = Evaluation.objects.create(user=user, filename="activities.csv", expected_emission=2, total_emission=1, rows=[])
        self.assertEqual(Evaluation.objects.filter(user=user, pk=evaluation.pk).count(), 1)

    def test_upload_results_and_report_flow(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(username="reporter", password="a-long-test-password")
        self.client.force_login(user)
        response = self.client.get("/home/")
        self.assertEqual(response.status_code, 200)
        upload = SimpleUploadedFile(
            "activities.csv",
            b"Activity,Emissions,Scope\nElectricity,500,2\n",
            content_type="text/csv",
        )
        response = self.client.post("/analyze/", {"excel_file": upload, "expected_emission": "1.0"})
        self.assertEqual(response.status_code, 302)
        results = self.client.get("/results/")
        self.assertEqual(results.status_code, 200)
        self.assertContains(results, "0.5")
        evaluation = Evaluation.objects.get(user=user)
        report = self.client.get(f"/reports/{evaluation.pk}.csv")
        self.assertEqual(report.status_code, 200)
        self.assertIn(b"Scope 2,0.5", report.content)

    def test_retrieved_guidance_keeps_pdf_source_citations(self):
        ingest = ModuleType("backend.rag.ingest")
        ingest.create_collection = lambda: SimpleNamespace(count=lambda: 1)
        retriever = ModuleType("backend.rag.retriever")
        retriever.search_guidance = lambda query, n_results: [{
            "text": "Scope 2 reporting guidance passage.",
            "source_filename": "Scope 2 Guidance.pdf",
            "page_number": 12,
            "distance": 0.2,
        }]
        evaluation = SimpleNamespace(scope1_emission=0, scope2_emission=1.25, scope3_emission=0)
        with patch.dict("sys.modules", {"backend.rag.ingest": ingest, "backend.rag.retriever": retriever}):
            result = retrieve_evaluation_guidance(evaluation)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["sections"][0]["evidence"][0]["source_filename"], "Scope 2 Guidance.pdf")
        self.assertEqual(result["sections"][0]["evidence"][0]["page_number"], 12)

    def test_results_page_displays_retrieved_guidance_citation(self):
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user(username="guidance-user", password="a-long-test-password")
        evaluation = Evaluation.objects.create(user=user, filename="activities.xlsx", expected_emission=3, total_emission=1.25, scope2_emission=1.25, rows=[])
        self.client.force_login(user)
        session = self.client.session
        session["evaluation_id"] = evaluation.pk
        session.save()
        guidance = {"status": "ready", "message": "", "sections": [{"label": "Scope 2 · Purchased energy", "review_check": "Verify the electricity records.", "evidence": [{"text": "Use the location-based method.", "source_filename": "Scope 2 Guidance.pdf", "page_number": 12}]}]}
        with patch("cwai.views.retrieve_evaluation_guidance", return_value=guidance):
            response = self.client.get("/results/")
        self.assertContains(response, "Use the location-based method.")
        self.assertContains(response, "Scope 2 Guidance.pdf, page 12")
