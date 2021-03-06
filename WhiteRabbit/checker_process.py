'''
    Copyright (c) 2012 Alexander Abbott

    This file is part of the Cheshire Cyber Defense Scoring Engine (henceforth
    referred to as Cheshire).

    Cheshire is free software: you can redistribute it and/or modify it under
    the terms of the GNU Affero General Public License as published by the
    Free Software Foundation, either version 3 of the License, or (at your
    option) any later version.

    Cheshire is distributed in the hope that it will be useful, but WITHOUT ANY
    WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
    FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for
    more details.

    You should have received a copy of the GNU Affero General Public License
    along with Cheshire.  If not, see <http://www.gnu.org/licenses/>.
'''
from __future__ import division
from copy import deepcopy, copy
from datetime import datetime, timedelta
from multiprocessing import Process, Event
import random
from Doorknob.MongoDBWrapper import MongoDBWrapper
from WhiteRabbit.check_types import InjectCheck, ServiceCheck, AttackerCheck

class CheckerProcess(Process):
    def __init__(self, team_id, checks, db_host, db_port, db_name, check_delay):
        super(CheckerProcess, self).__init__()
        self.team_id = team_id
        self.db = MongoDBWrapper(db_host, int(db_port), db_name)
        self.check_delay = int(check_delay)
        self.shutdown_event = Event()
        self.checks = []
        for check in checks:
            check_db_data = self.db.get_specific_check(check.check_id, check.check_class.check_type)
            if len(check_db_data) > 0:
                check_data = check_db_data[0]
                if issubclass(check.check_class, InjectCheck):
                    check_obj = check.check_class(check_data['machine'], team_id, db_host, db_port, db_name, check_data['time_to_check'])
                    self.checks.append(Checker(check.check_id, check_obj, check_obj.time_to_run))
                elif issubclass(check.check_class, (ServiceCheck, AttackerCheck)):
                    check_obj = check.check_class(check_data['machine'], team_id, db_host, db_port, db_name)
                    self.checks.append(Checker(check.check_id, check_obj, datetime.now()))
        random.shuffle(self.checks, random.random)

    def run(self):
        while not self.shutdown_event.is_set():
            self.run_checks()

    def run_checks(self):
        indices_to_remove = []
        for i in range(0, len(self.checks)):
            check = self.checks[i]
            check_obj = copy(check.object)
            now = datetime.now()
            print check.time_to_run, '<', now, '=', check.time_to_run < now
            if check.time_to_run < now:
                check_process = Process(target=check_obj.run_check)
                check_process.start()
                check_process.join(check_obj.timeout)
                if check_process.is_alive():
                    check_process.terminate()
                score = check_obj.score
                if issubclass(type(check_obj), InjectCheck):
                    self.db.complete_inject_check(check.id, self.team_id, datetime.now(), score)
                    #self.checks[:] = [obj for obj in self.checks if not obj == check]
                    indices_to_remove.append(i)
                elif issubclass(type(check_obj), ServiceCheck):
                    self.db.complete_service_check(check.id, self.team_id, datetime.now(), score)
                    check.timestamp = datetime.now() + timedelta(seconds=self.check_delay)
                elif issubclass(type(check_obj), AttackerCheck):
                    self.db.complete_attacker_check(check.id, self.team_id, datetime.now(), score)
                    check.timestamp = datetime.now() + timedelta(seconds=self.check_delay)
                self.db.calculate_scores_for_team(self.team_id)
            if self.shutdown_event.is_set():
                break
        indices_to_remove.sort(reverse=True)
        for i in indices_to_remove:
            del self.checks[i]

class Checker(object):
    def __init__(self, id, object, time_to_run):
        self.id = id
        self.object = object
        self.time_to_run = time_to_run
        self.timestamp = None