import os
import annotator.model as model

# Use in-memory database for testing
model.configure('sqlite:///:memory:')
model.rebuilddb()

