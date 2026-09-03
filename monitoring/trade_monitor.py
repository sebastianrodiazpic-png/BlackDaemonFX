class TradeMonitor:
    def __init__(self, engine):
        self.engine = engine

    def sync(self):
        return self.engine.sync_closed_trades()
