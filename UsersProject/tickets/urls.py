from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'tickets', views.TicketViewSet)
router.register(r'templates', views.TicketTemplateViewSet)
router.register(r'comments', views.TicketCommentViewSet)
router.register(r'attachments', views.TicketAttachmentViewSet)
router.register(r'routing-rules', views.RoutingRuleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
