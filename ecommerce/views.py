from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from datetime import timedelta
from .models import *
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_str
from .utils import generate_token, product_qty
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
import threading
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from .forms import CustomerLoginForm, CustomerRegisterForm
from django.contrib.auth.hashers import check_password, make_password
from django.contrib import messages
from django.urls import reverse

"""
    Start manage cart and check out
"""


def add_to_cart(request):
    product_id = request.GET.get('product_id')
    quantity = request.GET.get('quantity')
    try:
        product = Product.objects.get(id=product_id)
        cart_p = {str(product_id): {
            'name': product.name,
            'slug': product.slug,
            'imageURL': "" if not product.images.exists() else product.images.first().imageURL,
            'price': float(product.price),
            'quantity': int(quantity)
        }}
        if 'cart' in request.session:
            cart_data = request.session['cart']
            print(request.session['cart'])
            if str(product_id) in request.session['cart']:
                cart_data[str(product_id)]['quantity'] = int(cart_data[str(product_id)]['quantity']) + \
                                                         int(request.GET.get('quantity', 1))
                cart_data.update(cart_data)
            else:
                cart_data.update(cart_p)
            request.session['cart'] = cart_data
        else:
            request.session['cart'] = cart_p
        return JsonResponse({'success': True, 'cart': request.session['cart']})
    except Product.DoesNotExist:
        return JsonResponse({'success': False})


def delete_in_cart(request):
    product_id = request.GET.get('product_id')
    if 'cart' in request.session:
        cart = request.session['cart']
        del cart[product_id]
        if len(cart.items()) == 0:
            del request.session['cart']
        else:
            request.session['cart'] = cart
    return redirect('/cart/')


class ProductsCart(View):
    def get(self, request):
        cart = {}
        if 'cart' in request.session:
            cart = request.session['cart']
        context = {
            'cart': cart,
        }
        return render(request, 'product/cart.html', context)

    def post(self, request):
        if 'update_cart' in request.POST:
            product_ids = request.POST.getlist('product-id')
            quantities = request.POST.getlist('quantity')
            cart = {}
            if 'cart' in request.session:
                cart = request.session['cart']
                for product_id, quantity in zip(product_ids, quantities):
                    if int(quantity) == 0:
                        del cart[product_id]
                    else:
                        cart[product_id]['quantity'] = int(quantity)
                request.session['cart'] = cart
            return redirect('/cart/')
        elif 'checkout' in request.POST:
            quantity_errors = {}
            if 'cart' in request.session:
                cart = request.session['cart']
                for product_id, product_data in cart.items():
                    product = Product.objects.get(id=product_id)
                    product_quantity = product_qty(product)
                    if product_quantity < int(product_data['quantity']):
                        quantity_errors[product_id] = product_quantity
                if quantity_errors:
                    context = {'cart': cart, 'quantity_errors': quantity_errors}
                    return render(request, 'product/cart.html', context)
                return redirect('/checkout/')
            return redirect('/cart/')


class Checkout(View):
    def get(self, request):
        if not 'customer' in request.session:
            return redirect('/login/?next=/checkout/')
        if 'cart' in request.session:
            total_price = 0
            cart = request.session['cart']
            for key, value in cart.items():
                total_price += value['quantity'] * value['price']
            context = {
                'cart':cart,
                'total_price': total_price,
            }
            return render(request, 'customer/checkout.html', context)
        messages.add_message(request, messages.WARNING,"Giỏ hàng rỗng, vui lòng thêm sản phẩm vào giỏ.")
        return redirect('/cart/')
    def post(self, request):
        if 'cart' in request.session:
            name = request.POST.get('name')
            phone_number = request.POST.get('phone-number')
            shipping_address = request.POST.get('shipping-address')
            uid = request.session['customer']
            customer = Customer.objects.get(id=uid)
            if not shipping_address or shipping_address == "":
                shipping_address = customer.shipping_address
            cart = request.session['cart']
            purchase_order = PurchaseOrder(customer=customer,
                                           receiver_name=name,
                                           receiver_phone=phone_number,
                                           ordered_time=datetime.now(),
                                           shipping_address=shipping_address,
                                           status="PENDING")
            purchase_order.save()
            for key, val in cart.items():
                product = Product.objects.get(id=key)
                purchase_order_item = PurchaseOrderItem(product=product,
                                                        purchase_order=purchase_order,
                                                        quantity=val['quantity'],
                                                        price=product.price)
                purchase_order_item.save()
        return redirect('/')



"""
    End manage cart and check out
"""

"""
    Start manage product view
"""


def get_product(request):
    product_id = request.GET.get('product_id')
    product = Product.objects.get(id=product_id)
    images = []
    for image in product.images.all():
        images.append(image.imageURL)
    json = JsonResponse({
        'id': product.id,
        'name': product.name,
        'brand': product.brand.name,
        'brslug': product.brand.slug,
        'price': product.price,
        'description': product.description,
        'images': list(images)
    })
    print(json.content)
    return json


class HomePage(View):
    def get(self, request):
        # body
        time = datetime.now() - timedelta(days=30)

        new_products = Product.objects.filter(created_at__gte=time, is_active=True).order_by('created_at')
        feature_products = Product.objects.filter(is_feature=True, is_active=True)
        categories = Category.objects.filter(display_home=True).order_by('name')
        products_categories = {}
        for category in categories:
            if category.product_set.exists():
                products = category.product_set.filter(is_active=True).order_by('brand__name')[:8]
                products_categories[category] = products

        # context
        context = {
            'new_products': new_products,
            'feature_products': feature_products,
            'products_categories': products_categories,
            'time': time
        }
        template_name = 'product/index.html'
        return render(request, template_name, context)

    def post(self, request):
        pass


class SingleProduct(View):
    def get(self, request, slug):
        # body
        time = datetime.now() - timedelta(days=7)

        product = Product.objects.get(slug=slug)
        related_products = Product.objects.filter(
            Q(category=product.category,
              price__gte=float(product.price) * 0.7,
              price__lte=float(product.price) * 1.3) |
            Q(category=product.category,
              brand=product.brand,
              price__gte=float(product.price) * 0.7,
              price__lte=float(product.price) * 1.3), is_active=True).exclude(id=product.id).order_by('price')[:10]

        # context
        context = {
            'product': product,
            'related_products': related_products,
            'time': time
        }
        template_name = 'product/single-product.html'
        return render(request, template_name, context)

    def post(self, request):
        pass


class ProductsShop(View):
    def get(self, request, type=None):

        # body
        products_list = Product.objects.filter(is_active=True)
        time = datetime.now() - timedelta(days=30)
        if type == 'new':
            products_list = products_list.filter(created_at__gte=time).order_by("created_at")
            shop_name = "Sản phẩm mới"
        elif type == 'feature':
            products_list = products_list.filter(is_feature=True).order_by('created_at')
            shop_name = "Sản phẩm đặc trưng"
        else:
            return redirect('/')

        # filter list type and category
        types = InstrumentType.objects.filter(category__product__in=products_list).distinct()
        types_categories = {}
        for type in types:
            categories = Category.objects.filter(product__in=products_list, type=type).distinct()
            types_categories[type] = categories
        # filter list brands
        brands = Brand.objects.filter(product__in=products_list).distinct().annotate(
            num_products=Count('product')).order_by('-num_products')
        # process filters
        selected_categories = request.GET.getlist('categories')
        selected_brands = request.GET.getlist('brands')
        if selected_categories:
            products_list = products_list.filter(category__slug__in=selected_categories)
        if selected_brands:
            products_list = products_list.filter(brand__slug__in=selected_brands)

        # order
        order_by = request.GET.get('order-by')
        if order_by == "asc":
            products_list = products_list.order_by("price")
        elif order_by == "desc":
            products_list = products_list.order_by("-price")

        # pagination
        paginator = Paginator(products_list, 9)
        page = request.GET.get('page', 1)
        products = paginator.get_page(page)

        # context
        context = {
            'products': products,
            'shop_name': shop_name,
            'types_categories': types_categories,
            "brands": brands,
            "selected_categories": selected_categories,
            "selected_brands": selected_brands,
            "order_by": order_by,
            'time': time,
        }
        template_name = 'product/products-shop.html'
        return render(request, template_name, context)

    def post(self, request):
        pass


class SearchProduct(View):
    def get(self, request):
        query = request.GET.get('query')
        if query is None:
            return redirect('/')
        products_list = Product.objects.filter(Q(name__icontains=query) |
                                               Q(category__name__icontains=query) |
                                               Q(brand__name__icontains=query) |
                                               Q(category__type__name__icontains=query),
                                               is_active=True)

        time = datetime.now() - timedelta(days=30)

        # filter list type and category
        types = InstrumentType.objects.filter(category__product__in=products_list).distinct()
        types_categories = {}
        for type in types:
            categories = Category.objects.filter(product__in=products_list, type=type).distinct()
            types_categories[type] = categories
        # filter list brands
        brands = Brand.objects.filter(product__in=products_list).distinct().annotate(
            num_products=Count('product')).order_by('-num_products')
        # process filters
        selected_categories = request.GET.getlist('categories')
        selected_brands = request.GET.getlist('brands')
        if selected_categories:
            products_list = products_list.filter(category__slug__in=selected_categories)
        if selected_brands:
            products_list = products_list.filter(brand__slug__in=selected_brands)

        # order
        order_by = request.GET.get('order-by')
        if order_by == "asc":
            products_list = products_list.order_by("price")
        elif order_by == "desc":
            products_list = products_list.order_by("-price")

        # pagination
        paginator = Paginator(products_list, 9)
        page = request.GET.get('page', 1)
        products = paginator.get_page(page)

        # context
        context = {
            'query': query,
            'products': products,
            'types_categories': types_categories,
            "brands": brands,
            "selected_categories": selected_categories,
            "selected_brands": selected_brands,
            "order_by": order_by,
            'time': time,
        }
        template_name = 'product/products-search.html'
        return render(request, template_name, context)

    def post(self, request):
        pass


class ProductsByBrand(View):
    def get(self, request, slug):
        # body
        time = datetime.now() - timedelta(days=30)

        brand = Brand.objects.get(slug=slug)
        products_list = Product.objects.filter(brand=brand, is_active=True).order_by('created_at')

        # filter list by types and categories
        types = InstrumentType.objects.filter(category__product__in=products_list).distinct()
        types_categories = {}
        for type in types:
            categories = Category.objects.filter(product__in=products_list, type=type).distinct()
            types_categories[type] = categories

        # process filters
        selected_categories = request.GET.getlist('categories')
        if selected_categories:
            products_list = products_list.filter(category__slug__in=selected_categories)

        # order
        order_by = request.GET.get('order-by')
        if order_by == "asc":
            products_list = products_list.order_by("price")
        elif order_by == "desc":
            products_list = products_list.order_by("-price")

        # pagination
        paginator = Paginator(products_list, 9)
        page = request.GET.get('page', 1)
        products = paginator.get_page(page)

        # context
        context = {
            'types_categories': types_categories,
            "selected_categories": selected_categories,
            "order_by": order_by,
            'brand': brand,
            'products': products,
            'time': time,
        }
        template_name = 'product/products-by-brand.html'
        return render(request, template_name, context)

    def post(self, request):
        pass


class ProductsByType(View):
    def get(self, request, slug):

        type = InstrumentType.objects.get(slug=slug)
        # body
        products_list = Product.objects.filter(category__type__slug=slug, is_active=True)
        time = datetime.now() - timedelta(days=30)

        # filter list category
        categories = Category.objects.filter(product__in=products_list).distinct().annotate(
            num_products=Count('product')).order_by('-num_products')
        # filter list brands
        brands = Brand.objects.filter(product__in=products_list).distinct().annotate(
            num_products=Count('product')).order_by('-num_products')
        # process filters
        selected_categories = request.GET.getlist('categories')
        selected_brands = request.GET.getlist('brands')
        if selected_categories:
            products_list = products_list.filter(category__slug__in=selected_categories)
        if selected_brands:
            products_list = products_list.filter(brand__slug__in=selected_brands)

        # order
        order_by = request.GET.get('order-by')
        if order_by == "asc":
            products_list = products_list.order_by("price")
        elif order_by == "desc":
            products_list = products_list.order_by("-price")

        # pagination
        paginator = Paginator(products_list, 9)
        page = request.GET.get('page', 1)
        products = paginator.get_page(page)

        # context
        context = {
            'products': products,
            'shop_name': type.name,
            'categories': categories,
            "brands": brands,
            "selected_categories": selected_categories,
            "selected_brands": selected_brands,
            "order_by": order_by,
            'time': time,
        }
        template_name = 'product/products-by-type.html'
        return render(request, template_name, context)

    def post(self, request):
        pass


class ProductsByCategory(View):
    def get(self, request, slug):

        category = Category.objects.get(slug=slug)

        # body
        products_list = Product.objects.filter(category__slug=slug, is_active=True)
        time = datetime.now() - timedelta(days=30)

        # filter list brands
        brands = Brand.objects.filter(product__in=products_list).distinct().annotate(
            num_products=Count('product')).order_by('-num_products')

        # process filters
        selected_brands = request.GET.getlist('brands')
        if selected_brands:
            products_list = products_list.filter(brand__slug__in=selected_brands)

        # order
        order_by = request.GET.get('order-by')
        if order_by == "asc":
            products_list = products_list.order_by("price")
        elif order_by == "desc":
            products_list = products_list.order_by("-price")

        # pagination
        paginator = Paginator(products_list, 9)
        page = request.GET.get('page', 1)
        products = paginator.get_page(page)

        # context
        context = {
            'products': products,
            'shop_name': category.name,
            "brands": brands,
            "selected_brands": selected_brands,
            "order_by": order_by,
            'time': time,
        }
        template_name = 'product/products-by-type.html'
        return render(request, template_name, context)

    def post(self, request):
        pass


class ShowAllBrands(View):
    def get(self, request):
        # body
        brands_list = Brand.objects.all().order_by("name")

        # pagination
        paginator = Paginator(brands_list, 15)
        page = request.GET.get('page', 1)
        brands = paginator.get_page(page)

        # context
        context = {
            "brands": brands,
        }
        template_name = "product/all-brands.html"
        return render(request, template_name, context)

    def post(self, request):
        pass


"""
    End Product View --------------------------------
"""

"""
    Start Customer View -----------------------------
"""


class Login(View):
    def get(self, request):
        if not request.session.get('customer'):
            form = CustomerLoginForm()
            template_name = "customer/login.html"
            return render(request, template_name, {"form": form})
        return redirect('/')

    def post(self, request):
        next = request.POST.get("next")
        print(next)
        fail_next = f"/login/?next={next}" if next != "/" else "/login/"
        form = CustomerLoginForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            try:
                customer = Customer.objects.get(email=email)
                if check_password(password, customer.password):
                    if customer.is_verify:
                        request.session["customer"] = customer.id
                        return redirect(next)
                    messages.error(request, "Tài khoản chưa được xác thực.")
                    return redirect(fail_next)
                else:
                    messages.error(request, "Sai số điện thoại hoặc mật khẩu.")
                    return redirect(fail_next)
            except Customer.DoesNotExist:
                messages.error(request, "Sai số điện thoại hoặc mật khẩu.")
                return redirect(fail_next)
        else:
            return redirect(fail_next)


def logout(request):
    del request.session['customer']
    return redirect("/")


class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


def send_email(customer, request, template):
    current_site = get_current_site(request)
    email_subject = 'Xác thực tài khoản.'
    email_body = render_to_string(f'customer/{template}', {
        'customer': customer,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(customer.pk)),
        'token': generate_token.make_token(customer),
        'protocol': 'https' if request.is_secure() else 'http'
    })

    email = EmailMessage(subject=email_subject, body=email_body,
                         from_email=settings.EMAIL_FROM_USER,
                         to=[customer.email]
                         )
    if email.send():
        messages.add_message(request, messages.SUCCESS,
                             "Chúng tôi vừa gửi tin nhắn xác thực đến Email của bạn, vui lòng kiểm tra.")
    else:
        messages.add_message(request, messages.ERROR,
                             "Có lỗi khi gửi xác thực đến Email của bạn, hãy chắc chắn bạn nhập đúng Email.")
    # if not settings.TESTING:
    #     EmailThread(email).start()


def activate_user(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        customer = Customer.objects.get(pk=uid)

    except Exception as e:
        customer = None

    if customer and generate_token.check_token(customer, token):
        customer.is_verify = True
        customer.save()
        messages.add_message(request, messages.SUCCESS,
                             'Email đã được xác thực, bây giờ bạn đã có thể đăng nhập.')
        return redirect('/login/')

    return render(request, 'customer/activate-failed.html')


class Register(View):
    def get(self, request):
        if not request.session.get('customer'):
            form = CustomerRegisterForm()
            template_name = "customer/register.html"
            return render(request, template_name, {"form": form})
        return redirect('/')

    def post(self, request):
        form = CustomerRegisterForm(data=request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            phone_number = form.cleaned_data['phone_number']
            password = form.cleaned_data['password']
            confirm_password = form.cleaned_data['confirm_password']
            if Customer.objects.filter(email=email).exists():
                messages.add_message(request, messages.ERROR, "Email đã tồn tại.")
                return render(request, 'customer/register.html', {'form': form}, status=409)
            if Customer.objects.filter(phone_number=phone_number).exists():
                messages.add_message(request, messages.ERROR, "Số điện thoại đã tồn tại.")
                return render(request, 'customer/register.html', {'form': form}, status=409)
            if password != confirm_password:
                messages.add_message(request, messages.ERROR, "Mật khẩu và Mật khẩu xác nhận không khớp.")
                return render(request, "customer/register.html", {'form': form}, status=409)
            customer = Customer.objects.create(name=name, email=email, phone_number=phone_number,
                                               password=make_password(password))
            customer.save()
            send_email(customer, request, 'activate.html')
            return redirect(reverse('login'))
        else:
            return redirect('/register/')


class PasswordRecoverConfirm(View):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            customer = Customer.objects.get(pk=uid)
        except Exception as e:
            customer = None
        if customer and generate_token.check_token(customer, token):
            return render(request, 'customer/password-new.html', {'customer': customer})
        return render(request, 'customer/activate-failed.html')

    def post(self, request, uidb64, token):
        email = request.POST.get('email')
        customer = Customer.objects.get(email=email)
        new_password = request.POST.get('new-password')
        confirm_password = request.POST.get('confirm-password')
        if new_password != confirm_password:
            messages.add_message(request, messages.ERROR, "Mật khẩu mới và Mật khẩu xác nhận không khớp.")
            return render(request, 'customer/password-new.html', {'customer': customer})
        customer.password = make_password(new_password)
        customer.save()
        messages.add_message(request, messages.SUCCESS, "Lấy lại mật khẩu thành công.")
        return redirect('/login/')


class PasswordRecover(View):
    def get(self, request):
        if not request.session.get('customer'):
            return render(request, 'customer/forget-password.html')
        return redirect('/')

    def post(self, request):
        email = request.POST.get('email')
        trigger_cus = Customer.objects.filter(Q(email=email)).first()
        if trigger_cus:
            send_email(trigger_cus, request, 'password-recover-message.html')
            return redirect('/login/')
        else:
            messages.add_message(request, messages.ERROR, "Email không tồn tại, vui lòng kiểm tra lại.")
            return redirect('/password-recover/')


class PersonalInfo(View):
    def get(self, request):
        if not request.session.get('customer'):
            return redirect('/login/')
        uid = request.session.get('customer')
        customer = Customer.objects.get(pk=uid)
        return render(request, 'customer/personal.html', {'customer': customer})

    def post(self, request):
        tab = request.POST.get('tab')
        if tab == 'info':
            name = request.POST.get('name')
            phone_number = request.POST.get('phone-number')
            shipping_address = request.POST.get('address')
            if request.session.get('customer'):
                uid = request.session.get('customer')
                customer = Customer.objects.get(pk=uid)
                if Customer.objects.filter(phone_number=phone_number).exists():
                    if uid != Customer.objects.filter(phone_number=phone_number).first().pk:
                        messages.add_message(request, messages.ERROR, "Số điện thoại đã tồn tại.")
                        return redirect('/personal/')
                customer.name = name
                customer.phone_number = phone_number
                customer.shipping_address = shipping_address
                customer.save()
                messages.add_message(request, messages.SUCCESS, "Đổi thông tin thành công.")
                return redirect('/personal/')
            messages.add_message(request, messages.WARNING, "Bạn chưa đăng nhập, vui lòng đăng nhập để tiếp tục.")
            return redirect('/login/')
        elif tab == 'password':
            current_password = request.POST.get('current-password')
            new_password = request.POST.get('new-password')
            confirm_password = request.POST.get('confirm-password')
            if request.session.get('customer'):
                uid = request.session.get('customer')
                customer = Customer.objects.get(pk=uid)
                if check_password(current_password, customer.password):
                    if new_password == confirm_password:
                        customer.password = make_password(new_password)
                        customer.save()
                        messages.add_message(request, messages.SUCCESS, "Đổi mật khẩu thành công.")
                        return redirect('/personal/')
                    messages.add_message(request, messages.ERROR,
                                         "Mật khẩu mới và Mật khẩu xác nhận không khớp.")
                    return redirect('/personal/')
            messages.add_message(request, messages.WARNING, "Bạn chưa đăng nhập, vui lòng đăng nhập để tiếp tục.")
            return redirect('/login/')
        return redirect('/personal/')


"""
    End Customer View -------------------------------
"""
