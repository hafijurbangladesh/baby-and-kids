from django.http import JsonResponse
from .models import Category

def get_subcategories(request):
    parent_id = request.GET.get('parent_id')
    if parent_id:
        subcategories = Category.objects.filter(parent_id=parent_id).values('id', 'name')
        return JsonResponse(list(subcategories), safe=False)
    else:
        # Get root categories (categories with no parent)
        categories = Category.objects.filter(parent__isnull=True).values('id', 'name')
        return JsonResponse(list(categories), safe=False)
