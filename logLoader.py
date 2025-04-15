from PyQt5.QtCore import QThreadPool
from mainwidget import Worker
import re
class LogLoader():
    def __init__(self,files,progressCallback,completeCallback):
        self.files = files
        self.progressCallback = progressCallback
        self.completeCallback = completeCallback
    def LoadData(self):
        def divide_task(N:int, n:int)->'list[tuple[int,int]]':
            """
            Divide a task of length N into n jobs as evenly as possible.
            Returns a list of (start, end) index ranges for each job.
            """
            jobs = []
            base = N // n  # Base workload per job
            extra = N % n   # Remaining extra workload to distribute
            start = 0
            
            for i in range(n):
                # Distribute the extra workload among the first 'extra' jobs
                end = start + base + (1 if i < extra else 0) - 1
                jobs.append((start, end))
                start = end + 1
            
            return jobs

        self.threadDone = 0
        self.maxThreads = QThreadPool.globalInstance().maxThreadCount()//2
        self.workers = []
        val = list(self.files.values())
        keys = list(self.files.keys())
        
        job_sizes = divide_task(len(val),self.maxThreads)
        print(f"Using {self.maxThreads} threads")
        for i in range(self.maxThreads):
            job_size = job_sizes[i]
            v = val[job_size[0]:job_size[1]+1]
            k= keys[job_size[0]:job_size[1]+1]
            w = Worker(v,k)
            w.signals.progress.connect(self.progressCallback)
            w.signals.done.connect(self.completeCallback)
            self.workers.append(w)
            QThreadPool.globalInstance().start(w)
