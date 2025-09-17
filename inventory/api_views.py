from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Category

def get_subcategories(request):
    parent_id = request.GET.get('parent_id')
    if parent_id:
        subcategories = Category.objects.filter(parent_id=parent_id).values('id', 'name')
        return JsonResponse(list(subcategories), safe=False)
    else:
        categories = Category.objects.filter(parent__isnull=True).values('id', 'name')
        return JsonResponse(list(categories), safe=False)

def get_category_chain(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    chain = []
    current = category
    
    # Build the chain from current category up to root
    while current:
        chain.append({'id': current.id, 'name': current.name})
        current = current.parent
    
    # Reverse to get root->leaf order
    chain.reverse()
    return JsonResponse(chain, safe=False)
