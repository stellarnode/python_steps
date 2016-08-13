def get_start_time(schedules, duration):

    def convert_to_decimal(time):
        hm = time.split(":")
        return int(hm[0]) * 60 + int(hm[1])

    def convert_to_time_string(time):
        if time == None:
            return None
        else:
            h = int(time) / 60
            m = int(time) % 60
            if m < 10:
                m = "0" + str(m)
            if h < 10:
                h = "0" + str(h)
            return str(h) + ":" + str(m)

    def find_free_time(schedule):
        i = 0
        free = []
        if len(schedule) == 0:
            return free

        if (schedule[i][0] > 540) and (i == 0):
            free.append([540, schedule[i][0], (schedule[i][0] - 540)])

        while i < len(schedule) - 1:
            if (schedule[i][1] != schedule[i+1][0]):
                free.append([schedule[i][1], schedule[i+1][0],
                             (schedule[i+1][0] - schedule[i][1])])
            i = i + 1

        if schedule[-1][1] < 1140:
            free.append([schedule[-1][1], 1140, 1140 - schedule[-1][1]])

        return free

    def filter_by_duration(schedule):
        filtered = []
        for slot in schedule:
            if slot[2] >= duration:
                filtered.append(slot)
        return filtered

    def filter_by_earliest(schedules, fit):
        filtered = []
        for schedule in schedules:
            new_schedule = []
            for slot in schedule:
                if slot[1] > fit and fit + duration <= slot[1]:
                    new_schedule.append(slot)
            filtered.append(new_schedule)
        return filtered

    def check_fit(schedules, fit):
        candidates = []
        for schedule in schedules:
            for slot in schedule:
                if fit >= slot[0] and slot[1] > fit and fit + duration <= slot[1]:
                    candidates.append(slot)
        return candidates

    def map_schedule(schedule):
        converted_schedule = []
        for slot in schedule:
            slot = [convert_to_decimal(slot[0]),
                    convert_to_decimal(slot[1])]
            converted_schedule.append(slot)
        return converted_schedule

    # DRAFT #3
    def fit_to_schedules(schedules):

        if [] in schedules:
            return None

        fit = 540
        found = False

        while not (found or [] in schedules):

            if [] in schedules:
                fit = None
                found = True
                break

            for schedule in schedules:
                if schedule[0][0] > fit:
                    fit = schedule[0][0]

            schedules = filter_by_earliest(schedules, fit)

            if [] in schedules:
                found = True
                fit = None
                break
            else:
                candidates = check_fit(schedules, fit)
                if len(candidates) >= len(schedules):
                    found = True
                    break
                else:
                    candidates = []

        return fit


    print("Initial schedules: ", schedules)
    print("Initial duration: ", duration)
    decimal_schedules = map(map_schedule, schedules)
    print("Converted schedule to decimals: ", decimal_schedules)
    free_times = map(find_free_time, decimal_schedules)
    free_times = map(filter_by_duration, free_times)
    print("Free times found: ", free_times)
    if [] in free_times:
        return None
    else:
        fit = fit_to_schedules(free_times)
        print("Found this fit: ", convert_to_time_string(fit), " (for duration " + str(duration) + " min)")
        if fit == None:
            return None
        else:
            return convert_to_time_string(fit)





    # DRAFT #2

#     def fit_to_schedules(schedules):
#         if [] in schedules:
#             return None

#         candidates = []
#         fit = 540

#         while not(len(candidates) == 3 or [] in schedules):
#             candidates[0] = schedules[0][0]
#             if candidates[0][0] > fit:
#                 fit = candidates[0][0]
#                 print("Current fit: ", fit)

#             for i in range(1, len(schedules) - 1):
#                 to_compare = schedules[i][0]
#                 if (fit >= to_compare[0]) and (fit + duration <= to_compare[1]):
#                     fit = to_compare[0]
#                     print("Current fit: ", fit)
#                     candidates.append(schedules[i][0])
#                 elif fit > to_compare[1]:
#                     schedules[i].remove(to_compare)
#                     print("Removed ", to_compare, " since fit is GT slot end time")
#                 elif candidates[0][1] < to_compare[0]:
#                     schedules[0].remove(candidates[0])
#                     print("Removed ", candidates[0], " since end time of this slot is LT earliest with others")
#                     if not(len(schedules[0]) == 0):
#                         candidates[0] = schedules[0][0]
#                     else:
#                         fit = None
#                         break
#                 else:
#                     candidates.append(schedules[i][0])

#             if ([] in schedules):
#                 fit = None

#         return fit



    #####################################

    # DRAFT 1 (WORKING BUT WITH SOME BUGS)

#     def fit_to_schedules(schedules):
#         while [] not in schedules:
#             fit = 540
#             for schedule in schedules:
#                 if len(schedule) > 0 and schedule[0][0] > fit:
#                     fit = schedule[0][0]
#                     print("Current fit candidate: ", fit)
#             for schedule in schedules:
#                 if len(schedule) > 0 and fit > schedule[0][1]:
#                     print("...removing ", schedule[0], " since fit " + str(fit) + " is GT end of free slot")
#                     schedule.remove(schedule[0])
#             for schedule in schedules:
#                 if len(schedule) > 0 and schedule[0][0] > fit:
#                     fit = schedule[0][0]
#                     print("Current fit candidate: ", fit)
#             for schedule in schedules:
#                 mtg_end = fit + duration
#                 if len(schedule) > 0 and (mtg_end > schedule[0][1]):
#                     print("...removing ", schedule[0], " since mtg_end " + str(mtg_end) + " is GT end of free slot")
#                     schedule.remove(schedule[0])
# #                     if len(schedule) > 0 and schedule[0][0] > fit:
# #                         fit = schedule[0][0]
#
#
#             found = True
#             for i in range(0, len(schedules) - 1):
#                 if len(schedules[i]) == 0:
#                     fit = None
#                 elif not ((fit >= schedules[i][0][0]) and (fit + duration <= schedules[i][0][1]) and (fit + duration <= 1140)):
#                     found = False
#                     print("This fit doesn't work: ", fit)
#                     for sched in schedules:
#                         if len(sched) > 0 and sched[0][0] > fit:
#                             fit = sched[0][0]
#                 else:
#                     found = True
#             if found:
#                 break
#             elif [] in schedules:
#                 fit = None
#                 break
#             else:
#                 continue
#         print("Schedules after fitting...: ", schedules)
#         return fit


    #############################################

    # DRAFT #0

#     def fit_to_schedules(schedules):
#         while [] not in schedules:
#             fit = 540
#             for schedule in schedules:
#                 if len(schedule) > 0 and schedule[0][0] > fit:
#                     fit = schedule[0][0]
#                     print("Current fit candidate: ", fit)
#             for schedule in schedules:
#                 if len(schedule) > 0 and fit > schedule[0][1]:
#                     print("...removing ", schedule[0], " since fit is GT end of slot")
#                     schedule.remove(schedule[0])

#             for schedule in schedules:
#                 mtg_end = fit + duration
#                 if len(schedule) > 0 and (mtg_end > schedule[0][1]):
#                     print("...removing ", schedule[0], " since mtg_end is GT end of slot")
#                     schedule.remove(schedule[0])
#                     if len(schedule) > 0 and schedule[0][0] > fit:
#                         fit = schedule[0][0]

#             found = True
#             for i in range(0, len(schedules) - 1):
#                 if len(schedules[i]) == 0:
#                     found = False
#                     fit = None
#                 elif not ((fit >= schedules[i][0][0]) and (fit + duration <= schedules[i][0][1]) and (fit + duration <= 1140)):
#                     found = False
#                     print("This fit doesn't work: ", fit)
#                     print("...removing ", schedules[i][0])
#                     schedules[i].remove(schedules[i][0])
#                     fit = None
#                 else:
#                     fit = schedules[i][0][0]
#             if found:
#                 break
#             elif [] in schedules:
#                 fit = None
#                 break
#             else:
#                 continue
#         print("Schedules after fitting...: ", schedules)
#         return fit




####################################

### OLD STUFF

####################################



# def get_start_time(schedules, duration):

#     def convert_to_decimal(time):
#         hm = time.split(":")
#         return float(hm[0]) + float(hm[1]) / 60.0

#     def convert_to_time_string(time):
#         h = int(time)
#         m = int((time - h) * 60)
#         if m < 10:
#             m = "0" + str(m)
#         if h < 10:
#             h = "0" + str(h)
#         return str(h) + ":" + str(m)

#     def find_free_time(schedule):
#         i = 0
#         free = []
#         while i < len(schedule) - 2:
#             if (schedule[i][0] > 9.0) and (i == 0):
#                 free.append([9.0, schedule[i][0], (schedule[i][0] - 9.0) * 60])
#             if (schedule[i][1] != schedule[i+1][0]) and ((schedule[i+1][0] - schedule[i][1]) * 60 >= duration):
#                 free.append([schedule[i][1], schedule[i+1][0],
#                              (schedule[i+1][0] - schedule[i][0]) * 60])
#             i = i + 1
#         return free

#     def map_schedule(schedule):
#         converted_schedule = []
#         for slot in schedule:
#             slot = [convert_to_decimal(slot[0]),
#                     convert_to_decimal(slot[1])]
#             converted_schedule.append(slot)
#         return converted_schedule

#     def fit_to_schedules(schedules):
#         while [] not in schedules:
#             fit = 0
#             for schedule in schedules:
#                 if schedule[0][0] > fit:
#                     fit = schedule[0][0]
#             for schedule in schedules:
#                 mtg_end = fit + duration / 60.0
#                 if (mtg_end > schedule[0][1]):
#                     schedule.remove(schedule[0])
#                     if schedule[0][0] > fit:
#                         fit = schedule[0][0]
#             found = True
#             for i in range(0, len(schedules) - 1):
#                 if not ((fit >= schedules[i][0][0]) and (fit + duration / 60.0 <= schedules[i][0][1]) and (fit + duration / 60.0 <= 19.0)):
#                     found = False
#                     print("This one doesn't work: ", fit)
#                     schedules[i].remove(schedules[i][0])
#                     fit = None
#             if found:
#                 break
#             elif [] in schedules:
#                 fit = None
#                 break
#             else:
#                 continue
#         print("Schedules after fitting...: ", schedules)
#         return fit

#     print("Initial schedules: ", schedules)
#     print("Initial duration: ", duration)
#     decimal_schedules = map(map_schedule, schedules)
#     free_times = map(find_free_time, decimal_schedules)
#     print free_times
#     if [] in free_times:
#         return None
#     else:
#         fit = fit_to_schedules(free_times)
#         print("Found this fit: ", fit, " (for duration " + str(duration / 60.0) + " hours)")
#         if fit == None:
#             return None
#         else:
#             return convert_to_time_string(fit)
