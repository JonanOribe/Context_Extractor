class Company:
    def __init__(self,name,website,type):
        self.name=name
        self.website=website
        self.type=type
    def description(self):
        return '{} is type {} and has the website: {}'.format(self.name,self.type,self.website)