from flask import Flask, render_template ,request,redirect,flash,url_for
from flask_login import LoginManager
import pymongo
from bson.objectid import ObjectId

#工具和配饰的最大数
MAX_GJ=1
MAX_PS=2

client=pymongo.MongoClient("mongodb://localhost:27017/")
db=client["treasure"]
user_col=db["user"]
item_col=db["item"]
wild_col=db["wild"]
market_col=db["market"]

#user_col.delete_many({})
item_col.delete_many({})
wild_col.delete_many({})
market_col.delete_many({})

item1={
   "name":"屠龙宝刀","host_id":0,#0代表不被拥有
   "luck_value":15,"cap_value":0,
   "state":"wild","value":100
}
item2={
   "name":"木棍","host_id":0,#0代表不被拥有
   "luck_value":0,"cap_value":3,
   "state":"wild","value":15
}
item3={
   "name":"铁棍","host_id":0,#0代表不被拥有
   "luck_value":0,"cap_value":3,
   "state":"wild","value":15
}
item4={
   "name":"屠龙宝刀","host_id":0,#0代表不被拥有
   "luck_value":15,"cap_value":0,
   "state":"market","value":100
}
item5={
   "name":"木棍","host_id":0,#0代表不被拥有
   "luck_value":0,"cap_value":3,
   "state":"market","value":20
}
item6={
   "name":"铁棍","host_id":0,#0代表不被拥有
   "luck_value":0,"cap_value":3,
   "state":"market","value":15
}

item_col.insert_many([item1,item2,item3,item4,item5,item6])
wild_col.insert_many([item1,item2,item3])
market_col.insert_many([item4,item5,item6])

app = Flask(__name__)
app.secret_key='x1s586x'


@app.route("/")
def sign():
   return render_template("login.html")

@app.route("/index/<username>")
def index(username):
   return render_template("index.html",username=username)

@app.route("/earn/<username>",methods=['GET'])
def earn(username):
   myquery={"name":username}
   record=user_col.find_one(myquery)
   money=record["capability"]
   user_col.update_one(
      {"name":username},
      {"$inc":{"coin":money}}
   )
   return redirect(url_for('index',username=username))

@app.route("/hunt/<username>")
def hunt(username):
   myquery={"name":username}
   user=user_col.find_one(myquery)
   user_id=user['_id']
   luck=user["luck"]
   query={"luck_value":{"$lt":luck}}
   items=wild_col.find(query).sort([("luck_value",-1)])
   id=items[0]["_id"]
   item_col.update_one(
      {"_id":id},
      {"$set":{"state":"box","host_id":user_id}}
   )
   item=item_col.find_one({"_id":id})
   user_col.update_one(
      {"name":username},
      {"$push":{"item_box":item}}
   )
   wild_col.delete_one({"_id":id})
   return redirect(url_for('index',username=username))

@app.route("/signup", methods=['GET','POST'])
def signup():
   if request.method == 'POST':
      username = request.form.get('username')
      password = request.form.get('password')
      password2 = request.form.get('password2')
      if not all([username, password, password2]):
         flash('参数不完整')
      elif password != password2:
         flash('两次密码不一致，请重新输入')
      else:
         ##new_user = Users(username=username, password=password, id=None)
         user_col.insert_one({"name":username,"item_ps":[],"item_gj":[],"item_box":[],"coin":1000,
         "luck":20,"capability":20,"gj_num":0,"ps_num":0,"item_selling":[],"key":password})
         return render_template('login.html')
   return render_template('signup.html')

@app.route("/login", methods=['GET','POST'])
def login():
   if request.method == 'POST':
      username = request.form.get('username')
      password = request.form.get('password')
      if not all([username, password]):
         flash('参数不完整')
      result=user_col.find_one({"name":username})
      if result:
         return redirect(url_for('index',username=username))
      else:
         return render_template('login.html')
   return render_template('login.html')

@app.route("/dress/<username>")
def dress(username):
   myquery = {"name": username}
   user = user_col.find_one(myquery)
   item_box=user['item_box']
   ps_ids=user['item_ps']
   gj_ids=user['item_gj']
   item_ps=[]
   item_gj=[]
   for ps_id in ps_ids:
      ps=item_col.find_one({"_id":ObjectId(ps_id)})
      item_ps.append(ps)
   for gj_id in gj_ids:
      gj=item_col.find_one({"_id":ObjectId(gj_id)})
      item_gj.append(gj)
   return render_template('dress.html',item_box=item_box,item_ps=item_ps,item_gj=item_gj,username=username)

@app.route("/getchanged/<username>/<item_id>")
def getchanged(username,item_id):
   item=item_col.find_one({"_id":ObjectId(item_id)})
   user = user_col.find_one({"name": username})
   user_id = user['_id']
   user_col.update_one(
      {"name": username},
      {"$pull": {"item_box": {"_id": ObjectId(item_id)}}}
   )
   if item['luck_value']==0:#item为工具
      gj_num=user['gj_num']
      if gj_num==MAX_GJ:#工具栏已满,删除原来工具
         user_col.update_one(
            {"name": username},
            {"$pop": {"item_gj":-1}}
         )
      user_col.update_one(
         {"name": username},
         {"$push": {"item_gj": item_id}}
      )
      user_col.update_one(
         {"name": username},
         {"$set": {"capability": item['cap_value']}}
      )
      user_col.update_one(
         {"name": username},
         {"$set": {"gj_num": 1}}
      )
   else:#item为配饰
      ps_num=user['ps_num']
      if ps_num==MAX_PS:#配饰栏已满，删除第一个配饰
         user_col.update_one(
            {"name": username},
            {"$pop": {"item_ps":-1}}
         )
         item=item_col.find_one(
            {"_id":ObjectId}
         )
         user_col.update_one(
            {"name": username},
            {"$set": {"ps_num": 2}}
         )
      user_col.update_one(
         {"name": username},
         {"$push": {"item_ps": item_id}}
      )
      user_col.update_one(
         {"name":username},
         {"$inc": {"luck": item['luck_value']}}
      )
      user_col.update_one(
         {"name": username},
         {"$set": {"ps_num": 1}}
      )
   item_col.update_one(
      {"_id":ObjectId(item_id)},
      {"$set":{"host_id":user_id,"state":"using"}}
   )
   return redirect(url_for('dress',username=username))

@app.route("/market/<username>")
def market(username):
   items=market_col.find({})
   return render_template('market.html',items=items,username=username)

@app.route("/buy/<username>/<item_id>")
def buy(username,item_id):
   item = market_col.find_one({"_id": ObjectId(item_id)})
   host_id=item['host_id']
   value=item['value']
   user = user_col.find_one({"name": username})
   user_id = user['_id']
   coin=user['coin']
   remaining=coin-value
   if (remaining<0):
      return "钱不够了"
   else:
      item_col.update_one(
         {"_id":ObjectId(item_id)},
         {"$set":{"host_id":user_id,"state":"box"}}
      )
      item = item_col.find_one({"_id": ObjectId(item_id)})
      market_col.delete_one(
         {"_id":ObjectId(item_id)}
      )
      user_col.update_one(
         {"name":username},
         {"$push":{"item_box":item}}
      )
      user_col.update_one(
         {"name":username},
         {"$set":{"coin":remaining}}
      )
      user_col.update_one(
         {"_id":host_id},
         {"$inc":{"coin":value}}
      )
      user_col.update_one(
         {"_id":host_id},
         {"$pull":{"item_selling":{"_id":ObjectId(item_id)}}}
      )
   return redirect(url_for('market',username=username))

@app.route("/trade/<username>")
def trade(username):
   user=user_col.find_one({"name":username})
   items_box=user['item_box']
   items_selling=user['item_selling']
   return render_template('trade.html',username=username,items_box=items_box,items_selling=items_selling)

@app.route("/hangout/<username>/<item_id>")
def hangout(username,item_id):
   item_col.update_one(
      {"_id":ObjectId(item_id)},
      {"$set":{"state":"market"}}
   )
   item=item_col.find_one({"_id":ObjectId(item_id)})
   market_col.insert_one(item)
   user_col.update_one(
      {'name':username},
      {"$push":{"item_selling":item}}
   )
   user_col.update_one(
      {'name':username},
      {"$pull": {"item_box": {"_id": ObjectId(item_id)}}}
   )
   return redirect(url_for('trade',username=username))

@app.route("/retrieve/<username>/<item_id>")
def retrieve(username,item_id):
   item_col.update_one(
      {"_id":ObjectId(item_id)},
      {"$set":{"state":"box"}}
   )
   market_col.delete_one({"_id":ObjectId(item_id)})
   user_col.update_one(
      {'name':username},
      {"$pull":{"item_selling":{"_id":ObjectId(item_id)}}}
   )
   item=item_col.find_one({"_id":ObjectId(item_id)})
   user_col.update_one(
      {'name':username},
      {"$push": {"item_box": item }}
   )
   return redirect(url_for('trade',username=username))

if __name__ == '__main__':
   app.run(debug = True,port=5000)

