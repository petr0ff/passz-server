import errno
import json
import logging
import os
import time

import utils

if not os.path.exists(os.path.dirname("../log/")):
    try:
        os.makedirs(os.path.dirname("../log/"))
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise

logging.basicConfig(filename="../log/pass_machine_%s.log" % time.time(), level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger("requests").setLevel(logging.WARNING)


class Cycle(object):
    def __init__(self):
        self._project_name = utils.JIRA_PROJECT
        self._cycle_name = utils.TEST_CYCLE
        self._executions = self.get_all_executions_in_cycle()
        self._labels = utils.LABELS
        self._status_from = utils.STATUS_FROM
        self._status_to = utils.STATUS_TO

    def get_list_of_executions(self, offset):
        params = {
            "zqlQuery": "project=%s AND cycleName='%s'" % (self._project_name, self._cycle_name),
            "offset": offset
        }
        result = utils.get_request(utils.ZapiCalls.GET_ZQL_SEARCH, params)
        return result.json()

    def get_all_executions_in_cycle(self):
        """Get all executions, ignoring status and labels.
        """
        logging.info("Get all executions in Test Cycle %s" % self._cycle_name)
        processed = 0
        content = self.get_list_of_executions(processed)
        if not content["executions"]:
            logging.error("Failed to find executions for Test Cycle %s in project %s", self._cycle_name,
                          self._project_name)
            raise ValueError
        execs = []
        total_executions = content["totalCount"]
        while processed <= total_executions:
            for execution in content["executions"]:
                execs.append(execution)
            # 20 is max fetch size in zapi
            processed += 20
            content = self.get_list_of_executions(processed)
        logging.info("Done! Found executions: %s" % total_executions)
        return execs

    def get_executions_by_status_and_labels(self, status, labels=None):
        """Get executions by status and labels.

        :param status: status of test execution, for example UNEXECUTED
        :param labels: list of issue labels, like ["automated", "regression"].
                       Omit param if search by labels is not needed
        """
        if labels is None:
            labels = []
        logging.info("Find executions with status %s and labels %s in Test Cycle %s" % (status,
                                                                                        labels,
                                                                                        self._cycle_name))
        by_status = []
        logging.info("Executions search criteria: %s" % labels)
        logging.info("Total executions in cycle: %s" % len(self._executions))
        for execution in self._executions:
            if execution["status"]["name"] == status and set(labels).issubset(set(
                    x.encode('UTF8') for x in execution["labels"])):
                by_status.append(execution)
        logging.info("Total executions matching criteria: %s" % len(by_status))
        return by_status

    def get_execution_by_issue_key(self, issue_key):
        """Get executions by issue key.

        :param issue_key: the issue key of test execution, <project>-<issue_id>
        """
        logging.info("Find executions for issue %s in Test Cycle %s" % (issue_key, self._cycle_name))
        for execution in self._executions:
            if execution["issueKey"] == issue_key:
                logging.info("Found!")
                return execution
        logging.warn("Didn't find execution for issue %s" % issue_key)
        return None

    @staticmethod
    def update_execution_status(execution, status):
        if execution is not None:
            req = {
                "status": utils.STATUSES[status],
                "issueId": execution["issueId"],
                "projectId": execution["projectId"],
                "cycleId": execution["cycleId"],
                "versionId": execution["versionId"],
            }
            resp = utils.put_request(utils.ZapiCalls.PUT_EXECUTION + "/%s/execute" % execution["id"],
                                     json.dumps(req))
            logging.info("Test-case %s is now in status %s. Labels are: %s" % (
                execution["issueKey"], status, execution["labels"]))
            return resp

    @property
    def status_to(self):
        return self._status_to

    @property
    def status_from(self):
        return self._status_from

    @property
    def labels(self):
        return self._labels
