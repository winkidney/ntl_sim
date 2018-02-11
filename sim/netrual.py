NLT_accounts = {}


class Component:
    min_bid = float(1)
    minted = {}
    timestamp = 0
    auction_window = 300
    last_cycle = -1
    start_timestamp = -1
    current_cycle = 0
    accounts = NLT_accounts
    reserve = float(0)

    def __init__(self, token):
        self.token = token

    def __call__(self, timestamp: float):
        self.timestamp = timestamp
        if self.start_timestamp == -1:
            self.start_timestamp = timestamp
        if self.cycle > self.current_cycle:
            print('%s:: New cycle %s' % (self.token, self.cycle))
            self.update_status()
        return self

    @property
    def cycle(self) -> float:
        return int((self.timestamp - self.start_timestamp) / self.auction_window)

    @property
    def last_minted(self):
        return self.minted.get(self.last_cycle)

    def get_cycle(self, winner: str) -> list:
        return [
            c
            for c, v
            in self.minted.items()
            if v['sender'] == winner
        ]

    def send_token(self, sender, amount):
        print('sent %s NTL to %s' % (amount, sender))
        if sender not in self.accounts:
            self.accounts[sender] = amount
        else:
            self.accounts[sender] += amount
        print('Current balance %s' % self.accounts)

        return False

    def burn_token(self, sender, amount) -> bool:
        if sender not in self.accounts:
            return False
        if not self.accounts[sender] >= amount:
            return False
        else:
            self.accounts[sender] -= amount
            return True

    def update_status(self):
        self.update_cycle(self.cycle)
        if self.last_cycle >= 0:
            self.record_minted()

    def update_cycle(self, cycle):
        self.last_cycle = self.current_cycle
        self.current_cycle = cycle

    def record_minted(self):
        if self.last_minted:
            print('Found last Winner')
            self.send_token(self.last_minted['sender'], 1000)
            self.reserve += self.last_minted['bid']
            self.min_bid = self.last_minted['bid']

    def balance(self, sender) -> float:
        return self.accounts.get(sender, 0)

    @property
    def total_supply(self) -> float:
        return sum(list(self.accounts.values()))

    def verify_bid(self, bid) -> bool:
        return bid > self.min_bid

    def update_auction(self, bid: float, sender: str) -> True:
        params = dict(
            bid=bid,
            sender=sender
        )

        if self.cycle not in self.minted:
            self.minted[self.cycle] = params
            return True
        elif bid > self.minted[self.cycle]['bid']:
            self.minted[self.cycle].update(**params)
            return True
        return False

    def auction(self, sender: str, bid: float) -> bool:
        bid = float(bid)
        return self.verify_bid(bid) and self.update_auction(bid, sender)

    def redeem(self, sender: str, quantity: float) -> float:
        quantity = float(quantity)
        print('Redeeming Current accounts %s, redeem %s for %s' % (self.accounts, quantity, sender))
        assert self.cycle > 0
        redeemed = self.reserve / self.total_supply * quantity
        redeemed_percentage = redeemed / float(self.reserve)
        if not redeemed <= self.reserve:
            print('Redeem request is less than reserve')
            return False

        burned = self.burn_token(sender, quantity)
        if not burned:
            print('Failed on Burning')
            return False
        if burned:
            self.min_bid = (self.min_bid * redeemed_percentage)
            self.reserve -= redeemed
            print('Redeem Finished Current accounts %s' % self.accounts)
            return redeemed
