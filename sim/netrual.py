class Component:

    min_bid = 0
    minted = {}
    timestamp = 0
    auction_window = 3600
    last_cycle = 0
    current_cycle = 0
    accounts = {}

    @property
    def cycle(self) -> int:
        cycle = int(self.timestamp) % self.auction_window
        if cycle > self.current_cycle:
            self.update_status(cycle)
        return cycle

    @property
    def reserve(self) -> dict:
        return {
            v['sender']: v['bid']
            for r, v in self.minted.items()
            if r != self.cycle
        }

    @property
    def accounts(self):
        pass

    @property
    def last_minted(self):
        return self.minted[self.last_cycle]

    def send_token(self, sender, amount):
        if sender not in self.accounts:
            self.accounts[sender] = amount
        else:
            self.accounts[sender] += amount
        return

    def update_status(self, cycle):
        last_minted = self.last_minted
        self.min_bid = self.last_minted['bid']
        self.accounts[last_minted['sender']] = last_minted['bid']
        self.last_cycle = self.current_cycle
        self.current_cycle = cycle

    def balance(self, sender) -> int:
        return self.accounts.get(sender, 0)

    def verify_bid(self, bid):
        return bid > self.min_bid

    def update_auction(self, bid: int, sender: str) -> True:
        params = dict(
            bid=bid,
            sender=sender
        )

        if self.cycle not in self.minted:
            self.minted[self.cycle] = params
            return True
        elif bid > self.minted[self.cycle]['bid']:
            self.minted.update(**params)
            return True
        return False

    def auction(self, sender: str, bid: int) -> bool:
        return self.verify_bid(bid) and self.update_auction(bid, sender)

    def redeem(self, sender: int, quantity: int) -> bool:
        pass
