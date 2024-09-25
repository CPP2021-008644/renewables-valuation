# -*- coding: utf-8 -*-


import numpy as np







def LCvsElectrolyzerANDElectricityPrice(project, generalSpecs, capex_limits, electricity_price_limits, inf_time_series):
    import matplotlib.pyplot as plt
    import pandas as pd
    
    
    original_electrolyzer_cost = project.capex_dict['Electrolyzer'].amount
    original_replacement_cost = project.capex_dict['Stack Replacements'].amount
    original_el_price = generalSpecs.utilities_and_materials_dict['Electricity'].price
    
    
    power = project.main_product.capacity*project.feedstock_dict['Electricity'].usage*1000/24
    print(power)
    
    capex_range = np.linspace(capex_limits[0],capex_limits[1],20)*power
    electricity_price_range = np.linspace(electricity_price_limits[0],electricity_price_limits[1],20)
    
    X,Y = np.meshgrid(capex_range,electricity_price_range)

    Z = np.zeros((len(electricity_price_range),len(capex_range)))
    Z_df = np.zeros((int(np.floor(len(electricity_price_range)/4)),int(np.floor(len(capex_range)/4))))
    x_df = np.zeros(int(np.floor(len(capex_range)/4)))
    y_df = np.zeros(int(np.floor(len(electricity_price_range)/4)))
    
    
    for cap_idx in range(len(capex_range)):
        for el_idx in range(len(electricity_price_range)):
            
            project.capex_dict['Electrolyzer'].amount = capex_range[cap_idx]
            project.capex_dict['Stack Replacements'].amount = capex_range[cap_idx]*0.45
            generalSpecs.utilities_and_materials_dict['Electricity'].price = electricity_price_range[el_idx]
            project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
            
            
            
            Z[el_idx][cap_idx] = project.getLC(0.3,inf_time_series)
            if el_idx % 4 == 0 and cap_idx % 4 == 0:
                Z_df[Z_df.shape[0]-1 - int(np.floor(el_idx/4))][int(np.floor(cap_idx/4))] = np.round(Z[el_idx][cap_idx],2)
                x_df[int(np.floor(cap_idx/4))] = np.round(capex_range[cap_idx]/power,2)
                y_df[Z_df.shape[0]-1 - int(np.floor(el_idx/4))] = np.round(electricity_price_range[el_idx],2)
    
    
    project.capex_dict['Electrolyzer'].amount = original_electrolyzer_cost
    project.capex_dict['Stack Replacements'].amount = original_replacement_cost
    generalSpecs.utilities_and_materials_dict['Electricity'].price = original_el_price
    project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)    

    
    df = pd.DataFrame(Z_df, columns = x_df, index = y_df)


    fig, ax = plt.subplots()
    
    cont =ax.contourf(X/power,Y,Z, cmap=plt.get_cmap('Blues'))
    ax.plot(original_electrolyzer_cost/power,original_el_price, ls = 'None', markerfacecolor = 'orange', markeredgecolor = 'red', marker = 'o', mew = 1, label = 'H2B2')
    cummins_electrolyzer = 7000000
    ax.plot(cummins_electrolyzer/power,original_el_price, ls = 'None', markerfacecolor = 'black', markeredgecolor = 'black', marker = 'o', mew = 1, label = 'Cummins (Hydrogenics)')
    #plt.clabel(cont, inline=1, fontsize=10)
    
    ax.legend(loc = 'lower left')
    
    ax.set_xlabel('Electrolyzer cost (€/MW)')
    ax.set_ylabel('Electricity cost (€/MWh)')
    ax.set_title('Levelized Cost of Hydrogen (€)')
    fig.colorbar(cont)
    
    
    plt.show()
    return fig, df
    
    
    
def LCvsCapexANDElectricityPrice(project, generalSpecs, capex_limits, electricity_price_limits, inf_time_series):
    import matplotlib.pyplot as plt
    
    
    original_capex_dict = project.capex_dict
    original_capex = 0
    for key, cap in project.capex_dict.items():
        original_capex += cap.amount
    original_capex -= project.capex_dict['Stack Replacements'].amount
    original_el_price = generalSpecs.utilities_and_materials_dict['Electricity'].price
    
       
    project.capex_dict = {}
    project.addCost('Capex','capex', 8000000,project.start_time,project.start_time,-1,1,0,0)
    project.capex_dict['Capex'].setDepreciation(20,0)
    
    replacement_time = int(np.ceil(80000/(project.main_product.load_factor*365*24)))
    project.addCost('Stack replacements','capex', 0.45*8000000,project.start_time + replacement_time,project.end_time,replacement_time,1,0,0)
    project.capex_dict['Capex'].setDepreciation(20,0)
    
    capex_range = np.linspace(capex_limits[0],capex_limits[1],20)
    electricity_price_range = np.linspace(electricity_price_limits[0],electricity_price_limits[1],20)
    
    X,Y = np.meshgrid(capex_range,electricity_price_range)

    Z = np.zeros((len(electricity_price_range),len(capex_range)))
    
    for cap_idx in range(len(capex_range)):
        for el_idx in range(len(electricity_price_range)):
            
            project.capex_dict['Capex'].amount = capex_range[cap_idx]
            generalSpecs.utilities_and_materials_dict['Electricity'].price = electricity_price_range[el_idx]
            project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
            
            
            
            Z[el_idx][cap_idx] = project.getLC(0.3,inf_time_series)
            
            
    

    project.capex_dict = original_capex_dict
    generalSpecs.utilities_and_materials_dict['Electricity'].price = original_el_price
    project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)    

    
    



    fig, ax = plt.subplots()
    
    cont =ax.contourf(X/1000000,Y,Z, cmap=plt.get_cmap('Blues'))
    ax.plot(original_capex/1000000,original_el_price,markerfacecolor = 'orange', marker = 'o')
    #plt.clabel(cont, inline=1, fontsize=10)
    
    ax.set_xlabel('Initial CAPEX (m€)')
    ax.set_ylabel('Electricity cost (€/MWh)')
    ax.set_title('Levelized Cost of Hydrogen (€)')
    fig.colorbar(cont)
    
    
    plt.show()
    return fig



def LCvsElectricityPriceANDLoadFactor(project, generalSpecs, load_limits, electricity_price_limits, inf_time_series):
    import matplotlib.pyplot as plt
    import pandas as pd
    
    
    original_load = project.main_product.load_factor
    original_yearly_output = project.main_product.yearly_output
    original_el_price = generalSpecs.utilities_and_materials_dict['Electricity'].price

    
    load_range = np.linspace(load_limits[0],load_limits[1],20)
    electricity_price_range = np.linspace(electricity_price_limits[0],electricity_price_limits[1],20)
    
    X,Y = np.meshgrid(load_range,electricity_price_range)

    Z = np.zeros((len(electricity_price_range),len(load_range)))
    Z_df = np.zeros((int(np.floor(len(electricity_price_range)/4)),int(np.floor(len(load_range)/4))))
    x_df = np.zeros(int(np.floor(len(load_range)/4)))
    y_df = np.zeros(int(np.floor(len(electricity_price_range)/4)))
    
    
    for load_idx in range(len(load_range)):
        for el_idx in range(len(electricity_price_range)):
            
            project.main_product.load_factor = load_range[load_idx]
            project.main_product.yearly_output = load_range[load_idx]*365*project.main_product.capacity
            generalSpecs.utilities_and_materials_dict['Electricity'].price = electricity_price_range[el_idx]
            project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
            
            
            
            Z[el_idx][load_idx] = project.getLC(0.3,inf_time_series)
            if el_idx % 4 == 0 and load_idx % 4 == 0:
                Z_df[Z_df.shape[0]-1 - int(np.floor(el_idx/4))][int(np.floor(load_idx/4))] = np.round(Z[el_idx][load_idx],2)
                x_df[int(np.floor(load_idx/4))] = np.round(load_range[load_idx]*100,2)
                y_df[Z_df.shape[0]-1 - int(np.floor(el_idx/4))] = np.round(electricity_price_range[el_idx],2)
            
    

    project.main_product.load_factor = original_load
    project.main_product.yearly_output = original_yearly_output
    generalSpecs.utilities_and_materials_dict['Electricity'].price = original_el_price
    project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)    

    
    
    df = pd.DataFrame(Z_df, columns = x_df, index = y_df)


    fig, ax = plt.subplots()
    
    cont =ax.contourf(X*100,Y,Z, cmap=plt.get_cmap('Blues'))
    ax.plot(original_load*100,original_el_price,markerfacecolor = 'orange', markeredgecolor = 'red', marker = 'o')
    #plt.clabel(cont, inline=1, fontsize=10)
    
    ax.set_xlabel('Load Factor (%)')
    ax.set_ylabel('Electricity cost (€/MWh)')
    ax.set_title('Levelized Cost of Hydrogen (€)')
    fig.colorbar(cont)
    
    
    plt.show()
    return fig, df



def LCSpiderChart(project, generalSpecs, inf_time_series,tax_rate):
    import matplotlib.pyplot as plt
    
    
    original_dr = project.discount_rate
    original_el_price = generalSpecs.utilities_and_materials_dict['Electricity'].price
    original_electrolyzer = project.capex_dict['Electrolyzer'].amount
    original_replacements = project.capex_dict['Stack Replacements'].amount
    original_load = project.main_product.load_factor
    original_yearly_output = project.main_product.yearly_output
    
    length = 20
    lower = 0.7
    upper = 1.3
    
    
    base = np.linspace(lower,upper,length)
    
    dr_range = np.linspace(lower,upper,length)*project.discount_rate
    y_dr = np.linspace(lower,upper,length)
    
    el_price_range = np.linspace(lower,upper,length)*generalSpecs.utilities_and_materials_dict['Electricity'].price
    y_el_price = np.linspace(lower,upper,length)
    
    electrolyzer_range = np.linspace(lower,upper,length)*project.capex_dict['Electrolyzer'].amount
    y_electrolyzer = np.linspace(lower,upper,length)
    
    load_range = np.linspace(lower,upper,length)*project.main_product.load_factor
    y_load = np.linspace(lower,upper,length)
    
    
    
    
    
    for idx in range(len(dr_range)):
        
        project.discount_rate = dr_range[idx]
        y_dr[idx] = project.getLC(tax_rate,inf_time_series)
        project.discount_rate = original_dr
        
        generalSpecs.utilities_and_materials_dict['Electricity'].price = el_price_range[idx]
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_el_price[idx] = project.getLC(tax_rate,inf_time_series)
        generalSpecs.utilities_and_materials_dict['Electricity'].price = original_el_price
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
        
        project.capex_dict['Electrolyzer'].amount = electrolyzer_range[idx]
        project.capex_dict['Stack Replacements'].amount = electrolyzer_range[idx]*0.45
        y_electrolyzer[idx] = project.getLC(tax_rate,inf_time_series)
        project.capex_dict['Electrolyzer'].amount = original_electrolyzer
        project.capex_dict['Stack Replacements'].amount = original_replacements
        
        project.main_product.load_factor = load_range[idx]
        project.main_product.yearly_output = load_range[idx]*365*project.main_product.capacity
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_load[idx] = project.getLC(tax_rate,inf_time_series)
        project.main_product.load_factor = original_load
        project.main_product.yearly_output = original_yearly_output
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
    
    
    
    
    
    
    fig, ax = plt.subplots()
    ax.plot(base*100,y_dr, label = 'Cost of Capital')
    ax.plot(base*100,y_el_price, label = 'Electricity Cost')
    ax.plot(base*100,y_electrolyzer, label = 'Electrolyzer Cost')
    ax.plot(base*100,y_load, label = 'Load')
    ax.plot(100,project.getLC(tax_rate,inf_time_series), markerfacecolor = 'orange', markeredgecolor = 'red', marker = 'o')
    ax.legend()
    
    ax.set_xlim(lower*100,upper*100)
    ax.set_xlabel('Percentage of Base Case Value')
    
    #ax.set_ylim(bottom = np.amin(y))
    ax.set_ylabel('Levelized Cost of Hydrogen (€)')
    ax.set_title('LCOH Sensitivity')
    

    
    ax.grid(True)
    
    plt.show()  
    return fig












            
def NPVvsPrice(project,price_limits,inf_time_series):           
    import matplotlib.pyplot as plt
    
    original_price = project.main_product.target_price
    price_range = np.linspace(price_limits[0],price_limits[1],20)
    
    y = np.zeros(len(price_range))
    
    for idx in range(len(price_range)):
       project.main_product.target_price = price_range[idx]
       y[idx] = project.getNPV(0.3,inf_time_series)/1000000
    
       
    project.main_product.target_price = original_price
    
    fig, ax = plt.subplots()
    ax.plot(price_range,y, color = 'cornflowerblue')
    ax.plot(original_price,project.getNPV(0.3,inf_time_series)/1000000, markerfacecolor = 'orange', markeredgecolor = 'red', marker = 'o')
    
    ax.set_xlim(np.amin(price_range),np.amax(price_range))
    ax.set_xlabel('H2 Selling Price (€)')
    
    ax.set_ylim(bottom = np.amin(y))
    ax.set_ylabel('NPV (m€)')
    
    
    ax.set_title('Net Present Value vs Hydrogen Price')
    plt.grid(True)
    plt.show()
    return fig
    
    
    
    
def IRRvsPrice(project,price_limits,inf_time_series):           
    import matplotlib.pyplot as plt
    
    original_price = project.main_product.target_price
    price_range = np.linspace(price_limits[0],price_limits[1],20)
    
    y = np.zeros(len(price_range))
    
    for idx in range(len(price_range)):
       project.main_product.target_price = price_range[idx]
       y[idx] = project.getIRR(0.3,inf_time_series)*100
    
       
    project.main_product.target_price = original_price
    
    fig, ax = plt.subplots()
    ax.plot(price_range,y, color ='cornflowerblue')
    ax.plot(original_price,project.getIRR(0.3,inf_time_series)*100, markerfacecolor = 'orange', markeredgecolor ='red', marker = 'o')
    
    
    ax.set_xlim(np.amin(price_range),np.amax(price_range))
    ax.set_xlabel('H2 Selling Price (€)')
    
    #ax.set_ylim(bottom = np.amin(y))
    ax.set_ylabel('IRR (%)')
    ax.set_title('Internal Rate of Return vs Hydrogen Price')
    
    
    ax.grid(which='major', linewidth='1', color = 'white')
    
    plt.grid(True)
    
    plt.show()    
    return fig





    
    
def NPVvsPriceAndDiscountRate(project,price_limits,dr_limits, inf_time_series,tax_rate):
    import matplotlib.pyplot as plt
    
    
    original_price = project.main_product.target_price
    original_dr = project.discount_rate
    
    
       
    
    price_range = np.linspace(price_limits[0],price_limits[1],20)
    dr_range = np.linspace(dr_limits[0],dr_limits[1],20)
    
    X,Y = np.meshgrid(price_range,dr_range)

    Z = np.zeros((len(price_range),len(dr_range)))
    
    for price_idx in range(len(price_range)):
        for dr_idx in range(len(dr_range)):
            
            project.main_product.target_price = price_range[price_idx]
            project.discount_rate = dr_range[dr_idx]
            
            
            
            Z[dr_idx][price_idx] = project.getNPV(tax_rate,inf_time_series)/1000000
            
            
    
    
    
    project.main_product.target_price = original_price
    project.discount_rate = original_dr
    



    fig, ax = plt.subplots()
    
    cont =ax.contourf(X,Y*100,Z, cmap=plt.get_cmap('Blues'))
    ax.plot(original_price,original_dr*100, markerfacecolor = 'orange', markeredgecolor = 'red', marker = 'o')
    #plt.clabel(cont, inline=1, fontsize=10)
    
    ax.set_xlabel('Hydrogen Price (€)')
    ax.set_ylabel('Cost of Capital (%)')
    ax.set_title('NPV (m€)')
    fig.colorbar(cont)
    
    
    plt.show()
    return fig











def NPVSpiderChart(project, generalSpecs, inf_time_series,tax_rate):
    import matplotlib.pyplot as plt
    
    
    original_dr = project.discount_rate
    original_price = project.main_product.target_price
    original_el_price = generalSpecs.utilities_and_materials_dict['Electricity'].price
    original_electrolyzer = project.capex_dict['Electrolyzer'].amount
    original_replacements = project.capex_dict['Stack Replacements'].amount
    original_load = project.main_product.load_factor
    original_yearly_output = project.main_product.yearly_output
    
    length = 20
    lower = 0.9
    upper = 1.1
    
    
    base = np.linspace(lower,upper,length)
    
    dr_range = np.linspace(lower,upper,length)*project.discount_rate
    y_dr = np.linspace(lower,upper,length)
    
    price_range = np.linspace(lower,upper,length)*project.main_product.target_price
    y_price = np.linspace(lower,upper,length)
    
    el_price_range = np.linspace(lower,upper,length)*generalSpecs.utilities_and_materials_dict['Electricity'].price
    y_el_price = np.linspace(lower,upper,length)
    
    electrolyzer_range = np.linspace(lower,upper,length)*project.capex_dict['Electrolyzer'].amount
    y_electrolyzer = np.linspace(lower,upper,length)
    
    load_range = np.linspace(lower,upper,length)*project.main_product.load_factor
    y_load = np.linspace(lower,upper,length)
    
    
    
    
    
    for idx in range(len(dr_range)):
        
        project.discount_rate = dr_range[idx]
        y_dr[idx] = project.getNPV(tax_rate,inf_time_series)/1000000
        project.discount_rate = original_dr
        
        project.main_product.target_price = price_range[idx]
        y_price[idx] = project.getNPV(tax_rate,inf_time_series)/1000000
        project.main_product.target_price = original_price
        
        generalSpecs.utilities_and_materials_dict['Electricity'].price = el_price_range[idx]
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_el_price[idx] = project.getNPV(tax_rate,inf_time_series)/1000000
        generalSpecs.utilities_and_materials_dict['Electricity'].price = original_el_price
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
        
        project.capex_dict['Electrolyzer'].amount = electrolyzer_range[idx]
        project.capex_dict['Stack Replacements'].amount = electrolyzer_range[idx]*0.45
        y_electrolyzer[idx] = project.getNPV(tax_rate,inf_time_series)/1000000
        project.capex_dict['Electrolyzer'].amount = original_electrolyzer
        project.capex_dict['Stack Replacements'].amount = original_replacements
        
        project.main_product.load_factor = load_range[idx]
        project.main_product.yearly_output = load_range[idx]*365*project.main_product.capacity
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_load[idx] = project.getNPV(tax_rate,inf_time_series)/1000000
        project.main_product.load_factor = original_load
        project.main_product.yearly_output = original_yearly_output
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
    
    
    
    
    
    
    fig, ax = plt.subplots()
    ax.plot(base*100,y_dr, label = 'Cost of Capital')
    ax.plot(base*100,y_price, label = 'H2 Price')
    ax.plot(base*100,y_el_price, label = 'Electricity Cost')
    ax.plot(base*100,y_electrolyzer, label = 'Electrolyzer Cost')
    ax.plot(base*100,y_load, label = 'Load')
    ax.plot(100,project.getNPV(tax_rate,inf_time_series)/1000000, markerfacecolor = 'orange', markeredgecolor ='red', marker = 'o')
    ax.legend()
    
    ax.set_xlim(lower*100,upper*100)
    ax.set_xlabel('Percentage of Base Case Value')
    
    #ax.set_ylim(bottom = np.amin(y))
    ax.set_ylabel('NPV(m€)')
    ax.set_title('NPV Sensitivity')
    

    
    ax.grid(True)
    
    plt.show()  
    return fig






    
    
def IRRSpiderChart(project, generalSpecs, inf_time_series,tax_rate):
    import matplotlib.pyplot as plt
    
    
    original_price = project.main_product.target_price
    original_el_price = generalSpecs.utilities_and_materials_dict['Electricity'].price
    original_electrolyzer = project.capex_dict['Electrolyzer'].amount
    original_replacements = project.capex_dict['Stack Replacements'].amount
    original_load = project.main_product.load_factor
    original_yearly_output = project.main_product.yearly_output
    
    length = 20
    lower = 0.9
    upper = 1.1
    
    
    base = np.linspace(lower,upper,length)
    
    price_range = np.linspace(lower,upper,length)*project.main_product.target_price
    y_price = np.linspace(lower,upper,length)
    
    el_price_range = np.linspace(lower,upper,length)*generalSpecs.utilities_and_materials_dict['Electricity'].price
    y_el_price = np.linspace(lower,upper,length)
    
    electrolyzer_range = np.linspace(lower,upper,length)*project.capex_dict['Electrolyzer'].amount
    y_electrolyzer = np.linspace(lower,upper,length)
    
    load_range = np.linspace(lower,upper,length)*project.main_product.load_factor
    y_load = np.linspace(lower,upper,length)
    
    
    
    
    
    for idx in range(length):

        project.main_product.target_price = price_range[idx]
        y_price[idx] = project.getIRR(tax_rate,inf_time_series)*100
        project.main_product.target_price = original_price
        
        generalSpecs.utilities_and_materials_dict['Electricity'].price = el_price_range[idx]
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_el_price[idx] = project.getIRR(tax_rate,inf_time_series)*100
        generalSpecs.utilities_and_materials_dict['Electricity'].price = original_el_price
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
        
        project.capex_dict['Electrolyzer'].amount = electrolyzer_range[idx]
        project.capex_dict['Stack Replacements'].amount = electrolyzer_range[idx]*0.45
        y_electrolyzer[idx] = project.getIRR(tax_rate,inf_time_series)*100
        project.capex_dict['Electrolyzer'].amount = original_electrolyzer
        project.capex_dict['Stack Replacements'].amount = original_replacements
        
        project.main_product.load_factor = load_range[idx]
        project.main_product.yearly_output = load_range[idx]*365*project.main_product.capacity
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_load[idx] = project.getIRR(tax_rate,inf_time_series)*100
        project.main_product.load_factor = original_load
        project.main_product.yearly_output = original_yearly_output
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
    
    
    
    
    
    
    fig, ax = plt.subplots()
    ax.plot(base*100,y_price, label = 'H2 Price')
    ax.plot(base*100,y_el_price, label = 'Electricity Cost')
    ax.plot(base*100,y_electrolyzer, label = 'Electrolyzer Cost')
    ax.plot(base*100,y_load, label = 'Load')
    ax.plot(100,project.getIRR(tax_rate,inf_time_series)*100, markerfacecolor = 'orange', markeredgecolor ='red', marker = 'o')
    ax.legend()
    
    ax.set_xlim(lower*100,upper*100)
    ax.set_xlabel('Percentage of Base Case Value')
    
    #ax.set_ylim(bottom = np.amin(y))
    ax.set_ylabel('IRR (%)')
    ax.set_title('IRR Sensitivity')
    

    
    ax.grid(True)
    
    plt.show()  
    return fig









    
        
def PaybackvsPrice(project,price_limits,inf_time_series):           
    import matplotlib.pyplot as plt
    
    original_price = project.main_product.target_price
    price_range = np.linspace(price_limits[0],price_limits[1],200)
    
    y = np.zeros(len(price_range))
    
    for idx in range(len(price_range)):
       project.main_product.target_price = price_range[idx]
       y[idx] = project.getPayback(0.3,inf_time_series)
    
       
    project.main_product.target_price = original_price
    
    fig, ax = plt.subplots()
    ax.plot(price_range,y, color ='cornflowerblue')
    ax.plot(original_price,project.getPayback(0.3,inf_time_series), markerfacecolor = 'orange', markeredgecolor = 'red', marker = 'o')
    
    
    ax.set_xlim(np.amin(price_range),np.amax(price_range))
    ax.set_xlabel('H2 Selling Price (€)')
    
    ax.set_ylim(bottom = np.amin(y))
    ax.set_ylabel('Payback Period (years)')
    ax.set_title('Payback Period')
    
    
    ax.grid(which='major', linewidth='1', color = 'white')
    
    plt.grid(True)
    
    plt.show()     
    return fig










    
    
def PaybackSpiderChart(project, generalSpecs, inf_time_series,tax_rate):
    import matplotlib.pyplot as plt
    
    
    original_price = project.main_product.target_price
    original_el_price = generalSpecs.utilities_and_materials_dict['Electricity'].price
    original_electrolyzer = project.capex_dict['Electrolyzer'].amount
    original_replacements = project.capex_dict['Stack Replacements'].amount
    original_load = project.main_product.load_factor
    original_yearly_output = project.main_product.yearly_output
    
    length = 40
    lower = 0.7
    upper = 1.3
    
    
    base = np.linspace(lower,upper,length)
    
    price_range = np.linspace(lower,upper,length)*project.main_product.target_price
    y_price = np.linspace(lower,upper,length)
    
    el_price_range = np.linspace(lower,upper,length)*generalSpecs.utilities_and_materials_dict['Electricity'].price
    y_el_price = np.linspace(lower,upper,length)
    
    electrolyzer_range = np.linspace(lower,upper,length)*project.capex_dict['Electrolyzer'].amount
    y_electrolyzer = np.linspace(lower,upper,length)
    
    load_range = np.linspace(lower,upper,length)*project.main_product.load_factor
    y_load = np.linspace(lower,upper,length)
    
    
    
    
    
    for idx in range(length):

        project.main_product.target_price = price_range[idx]
        y_price[idx] = project.getPayback(tax_rate,inf_time_series)
        project.main_product.target_price = original_price
        
        generalSpecs.utilities_and_materials_dict['Electricity'].price = el_price_range[idx]
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_el_price[idx] = project.getPayback(tax_rate,inf_time_series)
        generalSpecs.utilities_and_materials_dict['Electricity'].price = original_el_price
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
        
        project.capex_dict['Electrolyzer'].amount = electrolyzer_range[idx]
        project.capex_dict['Stack Replacements'].amount = electrolyzer_range[idx]*0.45
        y_electrolyzer[idx] = project.getPayback(tax_rate,inf_time_series)
        project.capex_dict['Electrolyzer'].amount = original_electrolyzer
        project.capex_dict['Stack Replacements'].amount = original_replacements
        
        project.main_product.load_factor = load_range[idx]
        project.main_product.yearly_output = load_range[idx]*365*project.main_product.capacity
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_load[idx] = project.getPayback(tax_rate,inf_time_series)
        project.main_product.load_factor = original_load
        project.main_product.yearly_output = original_yearly_output
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
    
    
    
    
    
    
    fig, ax = plt.subplots()
    ax.plot(base*100,y_price, label = 'H2 Price')
    ax.plot(base*100,y_el_price, label = 'Electricity Cost')
    ax.plot(base*100,y_electrolyzer, label = 'Electrolyzer Cost')
    ax.plot(base*100,y_load, label = 'Load')
    ax.plot(100,project.getPayback(tax_rate,inf_time_series), markerfacecolor = 'orange', markeredgecolor ='red', marker = 'o')
    ax.legend()
    
    ax.set_xlim(lower*100,upper*100)
    ax.set_xlabel('Percentage of Base Case Value')
    
    #ax.set_ylim(bottom = np.amin(y))
    ax.set_ylabel('Payback Period (%)')
    ax.set_title('Payback Period Sensitivity')
    

    
    ax.grid(True)
    
    plt.show()  
    return fig



    
    
    
        



def RinvvsPriceAndDiscountRate(project,price_limits,dr_limits, inf_time_series,tax_rate):
    import matplotlib.pyplot as plt
    
    
    original_price = project.main_product.target_price
    original_dr = project.discount_rate
    
    
       
    
    price_range = np.linspace(price_limits[0],price_limits[1],40)
    dr_range = np.linspace(dr_limits[0],dr_limits[1],40)
    
    X,Y = np.meshgrid(price_range,dr_range)

    Z = np.zeros((len(price_range),len(dr_range)))
    
    for price_idx in range(len(price_range)):
        for dr_idx in range(len(dr_range)):
            
            project.main_product.target_price = price_range[price_idx]
            project.discount_rate = dr_range[dr_idx]
            
            
            
            Z[dr_idx][price_idx] = project.getReturnOnInvestment(tax_rate,inf_time_series)/1000000
            
            
    
    
    
    project.main_product.target_price = original_price
    project.discount_rate = original_dr
    



    fig, ax = plt.subplots()
    
    cont = ax.contourf(X,Y*100,Z, cmap=plt.get_cmap('Blues'))
    #ax.clabel(cont, inline=1, fontsize=8, colors = 'darkorange')
    ax.plot(original_price,original_dr*100, markerfacecolor = 'orange', markeredgecolor = 'red',marker = 'o')
 
    
    ax.set_xlabel('Hydrogen Price (€)')
    ax.set_ylabel('Cost of Capital (%)')
    ax.set_title('Return on Investment (m€)')
    fig.colorbar(cont)
    
    
    plt.show()
    return fig











def RinvSpiderChart(project, generalSpecs, inf_time_series,tax_rate):
    import matplotlib.pyplot as plt
    
    
    original_dr = project.discount_rate
    original_price = project.main_product.target_price
    original_el_price = generalSpecs.utilities_and_materials_dict['Electricity'].price
    original_electrolyzer = project.capex_dict['Electrolyzer'].amount
    original_replacements = project.capex_dict['Stack Replacements'].amount
    original_load = project.main_product.load_factor
    original_yearly_output = project.main_product.yearly_output
    
    length = 20
    lower = 0.9
    upper = 1.1
    
    
    base = np.linspace(lower,upper,length)
    
    dr_range = np.linspace(lower,upper,length)*project.discount_rate
    y_dr = np.linspace(lower,upper,length)
    
    price_range = np.linspace(lower,upper,length)*project.main_product.target_price
    y_price = np.linspace(lower,upper,length)
    
    el_price_range = np.linspace(lower,upper,length)*generalSpecs.utilities_and_materials_dict['Electricity'].price
    y_el_price = np.linspace(lower,upper,length)
    
    electrolyzer_range = np.linspace(lower,upper,length)*project.capex_dict['Electrolyzer'].amount
    y_electrolyzer = np.linspace(lower,upper,length)
    
    load_range = np.linspace(lower,upper,length)*project.main_product.load_factor
    y_load = np.linspace(lower,upper,length)
    
    
    
    
    
    for idx in range(len(dr_range)):
        
        project.discount_rate = dr_range[idx]
        y_dr[idx] = project.getReturnOnInvestment(tax_rate,inf_time_series)/1000000
        project.discount_rate = original_dr
        
        project.main_product.target_price = price_range[idx]
        y_price[idx] = project.getReturnOnInvestment(tax_rate,inf_time_series)/1000000
        project.main_product.target_price = original_price
        
        generalSpecs.utilities_and_materials_dict['Electricity'].price = el_price_range[idx]
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_el_price[idx] = project.getReturnOnInvestment(tax_rate,inf_time_series)/1000000
        generalSpecs.utilities_and_materials_dict['Electricity'].price = original_el_price
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
        
        project.capex_dict['Electrolyzer'].amount = electrolyzer_range[idx]
        project.capex_dict['Stack Replacements'].amount = electrolyzer_range[idx]*0.45
        y_electrolyzer[idx] = project.getReturnOnInvestment(tax_rate,inf_time_series)/1000000
        project.capex_dict['Electrolyzer'].amount = original_electrolyzer
        project.capex_dict['Stack Replacements'].amount = original_replacements
        
        project.main_product.load_factor = load_range[idx]
        project.main_product.yearly_output = load_range[idx]*365*project.main_product.capacity
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        y_load[idx] = project.getReturnOnInvestment(tax_rate,inf_time_series)/1000000
        project.main_product.load_factor = original_load
        project.main_product.yearly_output = original_yearly_output
        project.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
        
    
    
    
    
    
    
    fig, ax = plt.subplots()
    ax.plot(base*100,y_dr, label = 'Cost of Capital')
    ax.plot(base*100,y_price, label = 'H2 Price')
    ax.plot(base*100,y_el_price, label = 'Electricity Cost')
    ax.plot(base*100,y_electrolyzer, label = 'Electrolyzer Cost')
    ax.plot(base*100,y_load, label = 'Load')
    ax.plot(100,project.getReturnOnInvestment(tax_rate,inf_time_series)/1000000, markerfacecolor = 'orange', markeredgecolor = 'red', marker = 'o')
    ax.legend()
    
    ax.set_xlim(lower*100,upper*100)
    ax.set_xlabel('Percentage of Base Case Value')
    
    #ax.set_ylim(bottom = np.amin(y))
    ax.set_ylabel('Return on Investment (m€)')
    ax.set_title('Return on Investment Sensitivity')
    
    
    
    ax.grid(True)
    
    plt.show()  
    return fig












def exportPlots(project, generalSpecs, inflation_time_series, tax_rate):
    import matplotlib as plt
    carboneras = project
    inflation_factors = inflation_time_series
    
    
    directory = 'C:/Users/jbernabeu/Dropbox (Afirma Spain)/Mi PC (arfimai541)/H2/Hydrogen costs/python CF Analysis/informe_ci_marzo/images'
    
    plt.style.use('ggplot')
    
    #capex_limits in euros/kW
    electrolyzer_limits = [850,2000]
    el_price_limits = [0,70]
    fig, tab = LCvsElectrolyzerANDElectricityPrice(carboneras,generalSpecs,electrolyzer_limits,el_price_limits,inflation_factors)
    fig.savefig(directory + '/LCvsElectrolyzerAndElectricity.png')
    tab.to_csv(directory + '/LCvsElectrolyzerAndElectricity.csv')
    
    #LCOH vs Electricity price and load factor
    load_limits = [0.7,1]
    fig, tab = LCvsElectricityPriceANDLoadFactor(carboneras, generalSpecs, load_limits, el_price_limits, inflation_factors)
    fig.savefig(directory + '/LCvsLoadAndElectricity.png')
    tab.to_csv(directory + '/LCvsLoadAndElectricity.csv')
    
    
    #LCOH Spider Graph
    LCSpiderChart(carboneras, generalSpecs, inflation_factors,tax_rate).savefig(directory + '/LCspider.png')
    
    # NPV vs Price
    hy_price_limits = [2,10]
    NPVvsPrice(carboneras,hy_price_limits,inflation_factors).savefig(directory + '/NPVvsPrice.png')
    
    # NPV vs Cost of Capital and Price
    dr_limits = [0.05,0.15]
    NPVvsPriceAndDiscountRate(carboneras,hy_price_limits,dr_limits, inflation_factors,tax_rate).savefig(directory + '/NPVvsCostOfCapitalAndPrice.png')
    
    # NPV Spider Graph
    NPVSpiderChart(carboneras, generalSpecs, inflation_factors,tax_rate).savefig(directory + '/NPVspider.png')
    
    # IRR vs Price
    hy_price_limits = [5,10]
    IRRvsPrice(carboneras,hy_price_limits,inflation_factors).savefig(directory + '/IRRvsPrice.png')
    
    # IRR Spider Graph
    IRRSpiderChart(carboneras, generalSpecs, inflation_factors,tax_rate).savefig(directory + '/IRRspider.png')
    
    # Payback vs Price
    hy_price_limits = [5,10]
    PaybackvsPrice(carboneras,hy_price_limits,inflation_factors).savefig(directory + '/PaybackvsPrice.png')
    
    # Payback Spider Graph
    PaybackSpiderChart(carboneras, generalSpecs, inflation_factors, tax_rate).savefig(directory + '/Paybackspider.png')
    
    
    # Rinv vs Cost of Capital and Price
    hy_price_limits = [5,10]
    dr_limits = [0.05,0.15]
    RinvvsPriceAndDiscountRate(carboneras,hy_price_limits, dr_limits, inflation_factors,tax_rate).savefig(directory + '/RinvvsCostOfCapitalAndPrice.png')
    
    # Rinv Spider Graph
    RinvSpiderChart(carboneras, generalSpecs, inflation_factors,tax_rate).savefig(directory + '/Rinvspider.png')
    




    
    