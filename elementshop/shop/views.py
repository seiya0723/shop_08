from django.shortcuts import render,redirect


#TODO:ここにDRFに対応したビューを継承する。(DELETE,PUT,PATCHのリクエストボディを読むため。)
#https://noauto-nolife.com/post/django-rest-framework-need-ajax/
#https://noauto-nolife.com/post/django-rest-framework-changing/

#from django.views import View
from rest_framework.views import APIView as View

#Ajaxに対してJSONを返却する
from django.http.response import JsonResponse
#レンダリング結果を文字列で返す。
from django.template.loader import render_to_string


from .models import Product,Cart
from .forms import CartForm



class IndexView(View):

    def get(self, request, *args, **kwargs):

        context             = {}

        #ここで商品一覧表示時、検索をする。
        sort_list               = [
                                    {"key":"price","value":"値段が安い順"},
                                    {"key":"-price","value":"値段が高い順"},
                                ]
        keys                    = [ s["key"] for s in sort_list ]

        context["sort_list"]    = sort_list

        #並び替えが指定されている。
        if "order_by" in request.GET:

            #その並び替えが指定のリストの中にある。
            if request.GET["order_by"] in keys:
                context["products"] = Product.objects.order_by(request.GET["order_by"])

            else:
                context["products"] = Product.objects.all()
        else:
            context["products"] = Product.objects.all()


        return render(request, "shop/index.html", context)

index   = IndexView.as_view()


class ProductView(View):

    def get(self, request, pk, *args, **kwargs):
        #TODO:ここに商品の個別ページを作る

        product = Product.objects.filter(id=pk).first()

        if not product:
            return redirect("shop:index")

        context = {}
        context["product"]  = product

        return render(request, "shop/product.html", context)


    def post(self, request, pk, *args, **kwargs):
        #ここでユーザーのカートへ追加
        if request.user.is_authenticated:

            copied  = request.POST.copy()

            copied["user"]      = request.user.id
            copied["product"]   = pk

            form    = CartForm(copied)

            if not form.is_valid():
                print("バリデーションNG")
                return redirect("shop:index")


            print("バリデーションOK")

            #TIPS:ここで既に同じ商品がカートに入っている場合、レコード新規作成ではなく、既存レコードにamount分だけ追加する。
            cart    = Cart.objects.filter(user=request.user.id, product=pk).first()

            if cart:
                cleaned = form.clean()

                #TODO:ここでカートに数量を追加する時、追加される数量が在庫数を上回っていないかチェックする。上回る場合は拒否する。
                if cart.amount_change(cart.amount + cleaned["amount"]):
                    cart.amount += cleaned["amount"]
                    cart.save()
                else:
                    print("在庫数を超過しているため、カートに追加できません。")

            else:          
                #存在しない場合は新規作成
                form.save()

        else:
            print("未認証です")
            #TODO:未認証ユーザーにはCookieにカートのデータを格納するのも良い

        return redirect("shop:index")

product = ProductView.as_view()



#pkは、GETとPOSTの場合は商品ID、PUTとDELETEの場合はレビューID
class ProductCommentView(View):

    def get(self, request, pk, *args, **kwargs):
        #TODO:ここで利用者から投稿されたレビューをページネーションで閲覧できるようにする。
        pass

    def post(self, request, pk, *args, **kwargs):
        #TODO:ここで利用者から投稿されたレビューをDBに格納。
        pass

    def put(self, request, pk, *args, **kwargs):
        #TODO:ここで利用者から投稿されたレビューを編集する
        pass

    def delete(self, request, pk, *args, **kwargs):
        #TODO:ここで利用者から投稿されたレビューを削除する
        pass

product_comment = ProductCommentView.as_view()




class CartView(View):

    def get(self, request, *args, **kwargs):
        #ここでカートの中身を表示

        context             = {}

        if request.user.is_authenticated:

            carts   = Cart.objects.filter(user=request.user.id)

            context["total"]    = 0
            for cart in carts:
                context["total"] += cart.total()

            context["carts"]    = carts

        else:
            #TODO:未認証ユーザーにはCookie格納されたカートのデータを表示するのも良い
            pass

        return render(request, "shop/cart.html", context)


    def put(self, request, *args, **kwargs):
        #TODO:ここでカートの数量変更を受け付ける。
        
        data    = { "error":True }
        
        if "pk" not in kwargs:
            return JsonResponse(data)
        
        if request.user.is_authenticated:

            #リクエストがあったカートモデルのidとリクエストしてきたユーザーのidで検索する
            #(ユーザーで絞り込まない場合。第三者のカート内数量を勝手に変更されるため。)
            cart    = Cart.objects.filter(id=kwargs["pk"],user=request.user.id).first()

            if not cart:
                return JsonResponse(data)

            #CHECK:PUTメソッドにはリクエストボディが必要。この場合、リクエストボディを読むため、DRFが必要。
            #下記はDRFを実装してからコメントを外す。
            #TODO:ここでDRFのビュークラスを継承し、request.dataが読めるようにする。
            copied          = request.data.copy()
            copied["user"]  = request.user.id
            
            print(copied)

            #編集対象を特定して数量を変更させる。
            form    = CartForm(copied,instance=cart)

            if not form.is_valid():
                print("バリデーションNG")
                print(form.errors)
                return JsonResponse(data)


            print("バリデーションOK")

            cleaned = form.clean()

            if not cart.amount_change(cleaned["amount"]):
                print("数量が在庫数を超過。")
                return JsonResponse(data)

            #もし数量が規定値であれば編集して保存する。
            form.save()

            data["error"]   = False


            #TODO:ここでレンダリングを行い、レンダリング結果を文字列で返す(このレンダリング結果の文字列をJavaScriptに引き渡し、JavaScriptが所定の場所に貼り付ける。)
            context = {}
            carts   = Cart.objects.filter(user=request.user.id)

            context["total"]    = 0
            for cart in carts:
                context["total"] += cart.total()

            context["carts"]    = carts
            

            data["content"] = render_to_string("shop/cart_content.html", context, request)

            return JsonResponse(data)

        else:
            #TODO:未認証ユーザーにはCookie格納された内容を処理
            pass

        return JsonResponse(data)

    def delete(self, request, *args, **kwargs):
        #TODO:後にここでカート内の商品の削除処理を実行する。
        #CHECK:DELETEメソッドにはリクエストボディは不要。DELETEメソッドだけであればDRFは要らない。

        data    = {"error":True}

        if "pk" not in kwargs:
            return JsonResponse(data)

        if request.user.is_authenticated:
            cart    = Cart.objects.filter(id=kwargs["pk"],user=request.user.id).first()

            if not cart:
                return JsonResponse(data)

            cart.delete()
        
        data["error"]   = False

        return JsonResponse(data)

cart = CartView.as_view()


