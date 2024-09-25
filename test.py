# -*- coding: utf-8 -*-

import numpy as np
import renewablesValuation as rV

hy = rV.utilityOrMaterial("Hydrogen", "kg", 8)
hy_prod = rV.mainProduct(hy, 2000, 0.9, 5.62, 1, 0, 0, 2051)

replacement_years = [2022, 2023, 2025, 2040]

# b = hy_prod.getReplacementYears(0.1*24*365/80000,2022,0.95)


# print(b)

# hy_prod.setDecay(0.1*24*365/80000,b)

# a = hy_prod.getDecayFactors(2021,2059,2022)

# print(a)

"""
cf = np.array([-1000, 0,-10,0,40], dtype = float)


ri =rV.returnOnInvestment(cf,0.08)
new_cf = np.array([x for x in cf])
for idx in range(1,len(cf)):
    new_cf[idx] += ri
print(ri)    
print(rV.NPV(cf,0.08))
print(-cf[0])
print(cf)
print(new_cf)
print(rV.NPV(new_cf,0.08))
"""

"""
prices = np.linspace(5,10,50)

quant = 50
costs = 100


paybacks = np.array([])
for a in range(len(prices)):
    cf = np.zeros(30)
    cf[0] = -4000
    cf[1:] += quant*prices[a] - costs
    paybacks = np.append(paybacks, rV.paybackPeriod(cf))
    

plt.plot(prices,paybacks)

"""
"""
cf = np.zeros(3)
cf[0] = -1000
cf[1:] += 80
print(cf)
print(rV.returnOnInvestment(cf,0.08))
"""

""""------------// HYDROGEN WITH TYPICAL LITERATURE VALUES //------------- """


generalSpecs = rV.general()

generalSpecs.addUtilityOrMaterial("Hydrogen", "kg", 8)
generalSpecs.addUtilityOrMaterial("Electricity", "MWh", 25)
generalSpecs.addUtilityOrMaterial("Water", "kg", 0.00179)  # Why not 0.01?
generalSpecs.addUtilityOrMaterial("Nitrogen", "kg", 0.2783)
generalSpecs.addUtilityOrMaterial("KOH", "kg", 2.5)
generalSpecs.addUtilityOrMaterial("Oxygen", "kg", 0.0412)
generalSpecs.addUtilityOrMaterial("Hot Water", "kg", 0)

hy = generalSpecs.utilities_and_materials_dict["Hydrogen"]
el = generalSpecs.utilities_and_materials_dict["Electricity"]


testProject = rV.project("testProject", 2021, 31, 2022, 0.07)


testProject.setMainProduct(hy, 2000, 0.3, 5.62, 1, 0, 0)

testProject.addFeedstock("Electricity", "Electricity", usage=0.0576)
testProject.addFeedstock("Water", "Water", usage=15.29)  # Why not 10?
testProject.addFeedstock("Nitrogen", "Nitrogen", usage=0.00029)
# testProject.addFeedstock('KOH', usage = 0.0019)


# CAPITAL COSTS #

testProject.addCost(
    "Electrolyzer",
    "capex",
    3840000,
    testProject.start_time,
    testProject.start_time,
    -1,
    1,
    0,
    0,
)
testProject.capex_dict["Electrolyzer"].setDepreciation(10, 0)


# OPERATING COSTS #

testProject.addFeedstockCosts(generalSpecs.utilities_and_materials_dict)
testProject.addCost(
    "Other OPEX",
    "opex",
    0.03 * testProject.capex_dict["Electrolyzer"].amount,
    testProject.startup_time,
    testProject.end_time,
    1,
)

LCOH = np.round(testProject.getLC(0.3, np.ones(testProject.life)), 2)
print("LCOH without selling byproducts = " + str(LCOH))
