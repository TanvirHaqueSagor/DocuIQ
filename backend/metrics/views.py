from datetime import timedelta, date
from django.utils import timezone
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from core.permissions import IsInTenant
from ingest.models import IngestFile
from accounts.models import UserProfile

class DashboardSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInTenant]
    def get(self, request):
        tenant = getattr(request, 'tenant', None)
        docs = IngestFile.objects.filter(organization=tenant) if tenant else IngestFile.objects.filter(organization__isnull=True)
        total_documents = docs.count()
        # rough deltas (গতকাল তুলনা)
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        delta_documents = docs.filter(uploaded_at__date=today).count() - docs.filter(uploaded_at__date=yesterday).count()

        # org users
        org_users = 0
        if tenant:
            org_users = UserProfile.objects.filter(organization=tenant).count()

        payload = {
            "total_documents": total_documents,
            "delta_documents": delta_documents,
            "queries_last_7d": 0,        # আপনার query log এলে প্লাগ করুন
            "delta_queries": 0,
            "avg_answer_time_ms": None,  # প্লেসহোল্ডার
            "delta_answer_time": 0,
            "answer_confidence": None,   # প্লেসহোল্ডার
            "delta_confidence": 0,
            "org_users": org_users,
        }
        return Response(payload)

class UsageSeriesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsInTenant]
    def get(self, request):
        days = int(request.GET.get('days','14') or 14)
        tenant = getattr(request, 'tenant', None)
        qs = IngestFile.objects.filter(organization=tenant) if tenant else IngestFile.objects.filter(organization__isnull=True)
        start = timezone.now().date() - timedelta(days=days-1)
        # per-day counts
        by_day = (qs.filter(uploaded_at__date__gte=start)
                   .values('uploaded_at__date')
                   .annotate(count=Count('id'))
                   .order_by('uploaded_at__date'))
        # normalize timeline
        counts = { str(rec['uploaded_at__date']) : rec['count'] for rec in by_day }
        series = []
        for i in range(days):
            d = start + timedelta(days=i)
            series.append({"date": d.isoformat(), "count": counts.get(d.isoformat(), 0)})
        return Response(series)
