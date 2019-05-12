from django.shortcuts import render
from .models import Plug, Division, Day, Price
from users.models import Member, UserProfile
from django.http import HttpResponse
import datetime
import smtplib
import nodes.config_email as config
from django.contrib.auth.decorators import login_required
import calendar
from django.contrib.auth.models import User



# The price for Kwh for each power contract (price) of the simple contract
#electricity_costs = {
#     '1.15': 0.1595,
#     '2.3': 0.1598,
#     '3.45': 0.15690,
#     '4.6': 0.16050,
#     '5.75': 0.16170,
#     '6.9': 0.16190,
#    '10,35': 0.16200,
#    '13,8': 0.16330,
#    '17,25': 0.16420
#}


def send_email(message):
    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(config.EMAIL, config.PASSWORD)
        msg = message
        message = "Subject: {}\n\n{}".format("Energy Warning", msg).encode('utf-8').strip()
        server.sendmail(config.EMAIL, node.email, message)
        server.quit()
        print("Sucess: Email Sent!")
    except Exception as e:
        print("E-mail not sent!")
        print(e)


def update_daily(node):
    currentDT = datetime.datetime.now()
    day = currentDT.day
    if node.current_day != day:
        node.current_monthly_waste += node.current_daily_waste
        node.current_daily_waste = 0
        node.curr_day = day
    node.save()


def make_recommendation():
    maxz = 0
    second_maxz = 0
    max_plug = Plug()
    second_maxz_plug = Plug()
    for plug in Plug.objects.all():
        if(plug.current_daily_waste  > maxz):
            maxz = plug.current_daily_waste
            max_plug = plug
    for plug in Plug.objects.all():
        if(plug.current_daily_waste  > second_maxz and plug.current_daily_waste != maxz):
            second_maxz = plug.current_daily_waste
            second_maxz_plug = plug
    if(max_plug.current_daily_waste > 2 * second_maxz_plug.current_daily_waste):
        send_email(maxz.name + " has a much higher waste than the rest of the plugs, give it a look")

def make_recomendation_1():
    max_energy_per_member = 0
    second_max_per_member = 0

    max_member = UserProfile.members()
    second_member = UserProfile.members()

    for member in user.userprofile.members.all():
        if(member.monthly_waste > max_energy_per_member):
            max_energy_per_member = member.monthly_waste
            max_member = member

    for member in user.userprofile.members.all():
        if(member.monthly_waste > second_max_per_member and member.monthly_waste != max_energy_per_member):
            second_max_per_member = member.monthly_waste
            second_member = member

    if(max_member.monthly_waste > 2 * second_member.monthly_waste):
        send_email(max_member.name + " is using too much energy, be careful")

# def make_recomendation_2():
    #ver se o gasto da plug no mes anterior foi mt superior ao gasto deste mes e vice versa
    #caso seja, quer dizer que o eletrodomestico pode estar com defeito
    #nesse caso deve ser averiguado

# def make_recomendation_3():
    #ver horas de menor trafico, mas n temos os valores guardados por horas


def check_proximity_to_value(node, user):
    curr_value = node.current_daily_waste * user.energy_plan
    if(curr_value > (user.monthly_budget/calendar.monthrange(now.year, now.month)[1]) - 15):
        send_email("You are close to reaching your daily limit")
        make_recommendation()
        make_recomendation_1()


# Create your views here.
@login_required
def register_plug(request):
    if request.method == 'POST':
        now = datetime.datetime.now()
        try:
            division = request.user.userprofile.divisions.get(name=request.POST['division_name'])
        except Exception as e:
            division = Division(name = request.POST['division_name'])
            division.save()
            for i in range(1, calendar.monthrange(now.year, now.month)[1]+1):
                day = Day(day_number=i)
                day.save()
                division.days.add(day)
            request.user.userprofile.divisions.add(division)
            request.user.save()
            division.save()
        # division = Division.objects.get(name=request.POST['division_name'])

        product = Plug(activation_key = request.POST['activation_key'], name = request.POST['name'], current_day = now.day)
        product.save()
        for i in range(1, calendar.monthrange(now.year, now.month)[1]+1):
            day = Day(day_number=i)
            day.save()
            product.days.add(day)
        product.save()
        division.products.add(product)
        division.save()
        return HttpResponse('Product registered with success')
    else:
        return render(request, 'nodes/register_plug.html')

@login_required
def daily_rundown(request, division_name):
    division = request.user.userprofile.divisions.get(name=division_name)
    return render(request, 'nodes/daily_rundown.html', {'division': division})


#@login_required
#def product_rundown(request, division_name,product_name):
#    return HttpResponse('HEY')
#    division = request.user.userprofile.divisions.get(name=division_name)
#    product = division.products.get(name=product_name)
#    return render(request, 'nodes/product_rundown.html', {'product': product})

@login_required
def create_node(request):
    if request.method == 'POST':
        user = request.user
        currentDT = datetime.datetime.now()
        day = currentDT.day
        plug = Plug()
        plug.save()
        return HttpResponse(' User with activation key  ' + node.activation_key + ' created with ' + 'monthly budget set to ' + str(node.monthly_budget) + ' and your power plan is ' + str(node.power))
    else:
        return HttpResponse(' Only POST method is allowed ')

@login_required
def associate_member(request):
    if request.method == 'POST':
        user = request.user
        try:
            member = Member.objects.get(name=request.POST['name'])
        except Exception as e:
            member = Member(name=request.POST['name'])
        member.save()
        user.userprofile.members.add(member)
        division = user.userprofile.divisions.get(name=request.POST['division_name'])
        member.divisions.add(division)
        return HttpResponse('Member created with success')
    else:
        return render(request, 'nodes/associate_member.html')

@login_required
def member_waste(request, member_name):
    user = request.user
    member = user.userprofile.members.get(name=member_name)
    divisions = member.divisions.all()
    current_waste = 0
    div_price = []
    for division in divisions:
        number_of_members = division.member_set.all().count()
        current_waste += division.monthly_waste/number_of_members
        price = Price(name=division.name, price=division.monthly_waste/number_of_members)
        price.save()
        div_price.append(price)
    member.monthly_waste = current_waste
    member.save()

    return render(request, 'nodes/member_waste.html', {'divisions': divisions, 'member': member, 'member_name':member_name, 'current_waste':current_waste, 'div_price':div_price})

@login_required
def update_waste(request):
    if request.method == 'POST':
        node = Plug.objects.get(activation_key=request.META['HTTP_ACTIVATIONKEY'])
        update_daily(node)
        node.current_daily_waste += float(request.POST['read'])
        node.save()
        found = 0
        for userz in UserProfile.objects.all():
            for division in userz.divisions.all():
                for product in division.products.all():
                    if product.activation_key == request.META['HTTP_ACTIVATIONKEY']:
                        user = userz
                        div = division
                        found = 1
                        break
                if found == 1:
                    break
            if found == 1:
                break
        div.daily_waste += float(request.POST['read'])
        div.monthly_waste += float(request.POST['read'])
        day = div.days.get(day_number=datetime.datetime.now().day)
        day.energy_per_day += float(request.POST['read'])
        div.save()
        day.save()
        check_proximity_to_value(node, user)
        return HttpResponse('Waste changed')
    else:
        return HttpResponse(' Only POST method is allowed ')

# def update_waste(request):
#     return HttpResponse('HEY')
    # if request.method == 'POST':
    #     node = Plug.objects.get(activation_key=request.POST['activation_key'])
    #     update_daily(node)
    #     node.save()
    #     node.current_daily_waste += request.POST['read']
    #     node.save()
    #     check_proximity_to_value()
    #     return HttpResponse('Waste changed')
    # else:
    #     return HttpResponse(' Only POST method is allowed ')

# def set_monthly_budget(request):
#     return HttpResponse('HEY')
    # if request.method == 'POST':
    #     node = Plug.objects.get(activation_key=request.POST['activation_key'])
    #     node.monthly_budget = request.POST['monthly_budget']
    #     node.save()
    #     return HttpResponse('Monthly budget set to ' + str(node.monthly_budget) + ' in the node with the activation key ' + node.activation_key)
    # else:
    #     return HttpResponse(' Only POST method is allowed ')
