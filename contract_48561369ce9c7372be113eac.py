import smartpy as sp

class CharityContract(sp.Contract):
    def __init__(self, admin_address):
        self.init(
            admin=admin_address,
            totalDonations=sp.mutez(0),
            donations=sp.big_map(tkey=sp.TAddress, tvalue=sp.TMutez),
            notifications=sp.big_map(tkey=sp.TAddress, tvalue=sp.TRecord(time=sp.TTimestamp, message=sp.TString)),# Notification log
            fundraising_goal=sp.mutez(100000),
            progress=sp.nat(0)
        
        )

    def record_notification(self, sender, message):
        notifications = self.data.notifications
        notifications[sender] = sp.record(time=sp.timestamp_from_utc_now(), message=message)
        self.data.notifications = notifications
    
    def calculate_progress(self):
        return ((sp.utils.mutez_to_nat(self.data.totalDonations)* (100)) /sp.utils.mutez_to_nat(self.data.fundraising_goal))
    
    @sp.entry_point
    def donate(self):
        sp.verify(sp.amount > sp.utils.nat_to_mutez(0), "Donation amount must be greater than 0")
        sp.send(self.data.admin, sp.amount)
        self.data.totalDonations += sp.amount
        self.data.donations[sp.sender] = sp.amount
        self.record_notification(sp.sender, "Thank you for your donation!")  # Notify the donor
        sp.verify((self.data.totalDonations)<=self.data.fundraising_goal, "Fundraising goal achieved.")
        self.data.progress = self.calculate_progress()

    @sp.entry_point
    def withdraw(self):
        sp.verify(sp.sender == self.data.admin, "Only the admin can withdraw funds")
        sp.verify(self.data.totalDonations > sp.mutez(0), "No funds available for withdrawal")
        amount_to_withdraw = self.data.totalDonations
        sp.verify(amount_to_withdraw >= sp.balance, "Insufficient contract balance")
        sp.send(self.data.admin, amount_to_withdraw)
        self.data.totalDonations = sp.mutez(0)
        self.record_notification(sp.sender, "Funds successfully withdrawn!")  # Notify the admin

        
@sp.add_test(name="CharityContract")
def test():
    # Define a test scenario
    scenario = sp.test_scenario()

    # Define addresses
    admin_address = sp.address("KT1...")  # Replace with the admin's address
    donor1_address = sp.address("tz1...")  # Replace with a donor's address
    donor2_address = sp.address("tz2...")  # Replace with a donor's address
    donor3_address=sp.address("tz3...")   # Replace with a donor's address
    # Initialize the contract
    charity_contract = CharityContract(admin_address)
    scenario += charity_contract

    # Test donation
    scenario.h1("Test Donation")
    scenario += charity_contract.donate().run(sender=donor1_address, amount=sp.mutez(5000))
    scenario += charity_contract.donate().run(sender=donor2_address, amount=sp.mutez(5000))
    scenario += charity_contract.donate().run(sender=donor3_address, amount=sp.mutez(89000))


    # Test withdrawal
    scenario.h1("Test Withdrawal")
    scenario += charity_contract.withdraw().run(sender=admin_address, valid=False)


    # Display the contract state after the tests
    scenario.h1("Contract State After Tests")
    charity_contract = CharityContract(admin_address)
    scenario += charity_contract
