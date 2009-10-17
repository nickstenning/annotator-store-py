import os
import annotator.model as model

cwd = os.getcwd()
path = os.path.join(cwd, 'testsqlite.db')
dburi = 'sqlite:///%s' % path
model.repo.configure(dburi)
model.repo.rebuilddb()

