class Component:

    min_bid = 0
    minted = {}
    timestamp = 0
    auction_window = 3600
    last_cycle = 0
    current_cycle = 0
    accounts = {}
    reserve = 0

    def __init__(self, token):
        self.token = token

    @property
    def cycle(self) -> int:
        cycle = int(self.timestamp) % self.auction_window
        if cycle > self.current_cycle:
            self.update_status(cycle)
        return cycle

    @property
    def last_minted(self):
        return self.minted[self.last_cycle]

    @property
    def totaly_supply(self):
        return sum(list(self.reserve.values()))

    def get_cycle(self, winner: str) -> list:
        return [
            c
            for c, v
            in self.minted.items()
            if v['sender'] == winner
        ]

    def send_token(self, sender, amount):
        if sender not in self.accounts:
            self.accounts[sender] = amount
        else:
            self.accounts[sender] += amount
        return False

    def burn_token(self, sender, amount) -> bool:
        if not sender.balance >= amount:
            return False
        else:
            sender.balance -= amount
            return True

    def update_status(self, cycle):
        last_minted = self.last_minted
        self.send_token(self.last_minted['sender'], 1000)
        self.reserve += self.last_minted['bid']

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

    def redeem(self, sender: int, quantity: int) -> int:
        redeemed = (self.min_bid - quantity) * quantity / 2
        if not redeemed <= self.reserve:
            return False

        burned = self.burn_token(sender, quantity)
        if not burned:
            return False
        if burned:
            self.min_bid = self.min_bid - quantity
            return redeemed
