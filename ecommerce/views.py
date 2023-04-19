from django.shortcuts import render, redirect
from django.views import View

# Create your views here.

"""
Product management
"""
class Home(View):
    def get(self, request):
        return render(request, 'product/index.html', {})
    def post(self):
        pass

class SingleProduct(View):
    def get(self, request):
        return render(request, 'product/single-product.html', {})
    def post(self,request):
        pass

