import os
import annotator.model as model

cwd = os.getcwd()
path = os.path.join(cwd, 'db/test.sqlite3')
dburi = 'sqlite:///%s' % path
model.repo.configure(dburi)
model.repo.rebuilddb()

