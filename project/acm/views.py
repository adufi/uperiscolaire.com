from django.shortcuts import render

# Create your views here.

def shop_buy (request, pk=0):
    return render(request, 'client/Shop/Buy.html')

def shop_cannot_buy (request, pk=0):
    return render(request, 'client/Shop/CannotBuy.html')

def shop_view (request, pk=0):
    return render(request, 'client/Shop/View.html')

def shop_summary (request, pk=0):
    return render(request, 'client/Shop/Summary.html')

def shop_summary_dev (request, pk=0):
    return render(request, 'client/Shop/Summary-dev.html')

def shop_children (request, pk=0):
    return render(request, 'client/Shop/Children.html')