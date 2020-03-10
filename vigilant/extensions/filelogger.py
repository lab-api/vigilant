import os

class FileLogger:
    def __init__(self, filename):
        self.filename = filename

    def update(self, data):
        ''' Append the latest measurement to file. If the file does not exist,
            headers matching the columns in self.data are written first.
            Args:
                data (pandas.DataFrame): the most recent measurement
        '''
        if not os.path.isfile(self.filename):
            data.to_csv(self.filename, header=True)
        else:
            data.to_csv(self.filename, mode='a', header=False)
