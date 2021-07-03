from math import sqrt
from scipy.special import ndtri
import numpy as np
import pandas as pd

def _proportion_confidence_interval(r, n, z):

    A = 2 * r + z ** 2
    B = z * sqrt(z ** 2 + 4 * r * (1 - r / n))
    C = 2 * (n + z ** 2)
    return (str(round(((A - B) / C) * 100,2)) + '%', str(round(((A + B) / C)*100,2)) + '%')


def sensitivity_and_specificity_with_confidence_intervals(TP, FP, FN, TN, alpha=0.95):
    #
    z = -ndtri((1.0 - alpha) / 2)

    # Compute sensitivity using method described in [1]
    sensitivity_point_estimate = TP / (TP + FN)
    sensitivity_confidence_interval = _proportion_confidence_interval(TP, TP + FN, z)

    # Compute specificity using method described in [1]
    specificity_point_estimate = TN / (TN + FP)
    specificity_confidence_interval = _proportion_confidence_interval(TN, TN + FP, z)

    # Compute PPV and NPV
    PPV_point_estimate = TP / (TP + FP)
    NPV_point_estimate = TN / (TN + FN)
    PPV_confidence_interval = _proportion_confidence_interval(TP, TP + FP, z)
    NPV_confidence_interval = _proportion_confidence_interval(TN, TN + FN, z)

    return sensitivity_point_estimate, specificity_point_estimate, sensitivity_confidence_interval, specificity_confidence_interval, PPV_point_estimate, PPV_confidence_interval, NPV_point_estimate, NPV_confidence_interval


def days_matching_with_confidence_interval(same, next, week, twoweek, month, total):
    if same + next + week + twoweek + month + past > total:
        total = same + next + week + twoweek + month + past
    zero_day_point = same / total
    one_day_point = (same + next) / total
    week_point = (same + next + week) / total
    two_week_point = (same + next + week + twoweek) / total
    month_point = (same + next + week + twoweek + month) / total

    zero_day_conf = sqrt(((zero_day_point * (1-zero_day_point)) / total)) * 1.96
    one_day_conf = sqrt(((one_day_point * (1-one_day_point)) / total)) * 1.96
    week_conf = sqrt(((week_point * (1-week_point)) / total)) * 1.96
    two_week_conf = sqrt(((two_week_point * (1-two_week_point)) / total)) * 1.96
    month_conf = sqrt(((month_point * (1-month_point)) / total)) * 1.96

    zero_day_conf = (str(round((zero_day_point - zero_day_conf) * 100, 2)) + '%', str(round((zero_day_point + zero_day_conf) * 100, 2)) + '%')
    one_day_conf = (str(round((one_day_point - one_day_conf) * 100, 2)) + '%', str(round((one_day_point + one_day_conf) * 100, 2)) + '%')
    week_conf = (str(round((week_point - week_conf) * 100, 2)) + '%', str(round((week_point + week_conf) * 100, 2)) + '%')
    two_week_conf = (str(round((two_week_point - two_week_conf) * 100, 2)) + '%', str(round((two_week_point + two_week_conf) * 100, 2)) + '%')
    month_conf = (str(round((month_point - month_conf) * 100, 2)) + '%', str(round((month_point + month_conf) * 100, 2)) + '%')

    zero_day_point = str(round(zero_day_point * 100, 2)) + '%'
    one_day_point = str(round(one_day_point * 100, 2)) + '%'
    week_point = str(round(week_point * 100, 2)) + '%'
    two_week_point = str(round(two_week_point * 100, 2)) + '%'
    month_point = str(round(month_point * 100, 2)) + '%'

    return zero_day_point, zero_day_conf, one_day_point, one_day_conf, week_point, week_conf, two_week_point, two_week_conf, month_point, month_conf


counts = [
236,
88,
1691,
25
]

days = [
214,
16,
3,
0,
0,
3
]

TP = counts[0]
FP = counts[1]
TN = counts[2]
FN = counts[3]

zeroDay = days[0]
oneDay = days[1]
sevenDay = days[2]
fifteenday = days[3]
thirtyDay = days[4]
past = days[5]

a = 0.95
sensitivity_point_estimate, specificity_point_estimate, sensitivity_confidence_interval, specificity_confidence_interval, PPV, PPV_confidence, NPV, NPV_confidence \
    = sensitivity_and_specificity_with_confidence_intervals(TP, FP, FN, TN, alpha=a)
print("Sensitivity: %f, Specificity: %f" % (sensitivity_point_estimate*100, specificity_point_estimate*100))
print("sensitivity:", '(' + ', '.join(sensitivity_confidence_interval) + ')')
print("specificity:", '(' + ', '.join(specificity_confidence_interval) + ')')
print("PPV: %f, NPV: %f" % (PPV*100, NPV*100))
print("PPV:", '(' + ', '.join(PPV_confidence) + ')')
print("NPV:", '(' + ', '.join(NPV_confidence) + ')')
print("")

zdp, zdc, odp, odc, wp, wc, twp, twc, mp, mc = days_matching_with_confidence_interval(zeroDay, oneDay, sevenDay, fifteenday, thirtyDay, TP)
print('zero day')
print(zdp)
print('(' + ', '.join(zdc) + ')')

print('one day')
print(odp)
print('(' + ', '.join(odc) + ')')

print('week')
print(wp)
print('(' + ', '.join(wc) + ')')

print('two week')
print(twp)
print('(' + ', '.join(twc) + ')')

print('month')
print(mp)
print('(' + ', '.join(mc) + ')')

ar=np.array([[TP, FP],[FN, TN]])
df=pd.DataFrame(ar, columns=["Syapse Deceased", "Syapse Alive"])
df.index=["NDI Deceased", "NDI Alive"]

# Chi-Squared calculation
from scipy.stats import chi2_contingency
print("Chi squared with Yates' Correction is - " , chi2_contingency(ar)[0], "\nWith a p-value of - ", chi2_contingency(ar)[1])
print("Chi squared without Yates Correction is - " , chi2_contingency(ar, correction=False)[0], "\nWith a p-value of - ", chi2_contingency(ar, correction=False)[1])