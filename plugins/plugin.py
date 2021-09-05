class Plugin:
    class Decorators:
        def __init__(self, func):
            self.func = func
        def __call__(self, name):
            self.args[name] = self.func

    @Decorators('help')
    def helper(self):
        print('hi')


if __name__ == "__main__":
    test = Plugin()
    for a, b in test.Decorators.args.items():
       pass

    print({a:b.__name__ for a, b in test.Decorators.args.items()})