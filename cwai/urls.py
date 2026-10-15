
from django.urls import path
from . import views

urlpatterns = [
    # Login page
    path('', views.login_view, name='login'),

    # Signup page
    path('signup/', views.signup_view, name='signup'),

    # Home page after login
    path('home/', views.home_view, name='home'),

    # Process Excel file and calculate carbon emissions
    path('analyze/', views.analyze_view, name='analyze'),

    # Loading page during processing
    path('loading/', views.loading_view, name='loading'),

    # Display calculated emissions and RAG recommendations
    path('results/', views.results_view, name='results'),
    path('reports/<int:evaluation_id>.csv', views.report_view, name='report'),

    # Logout
    path('logout/', views.logout_view, name='logout'),
]
