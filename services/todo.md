MVP REQUIREMENTS FOR DIGITAL STORE
SHOP OWNER:
Admin should be able to add products, modify their name, description, category, images, prices etc., delete them, and temporarily hide them.
Admin should be able to add and remove categories.
Admin should be able to login into the store with their email and password, receive a session token, and be able to logout, rotate session token when it is about to end. ✅
Admin should be able to see every order with its current state.
Admin should be able to manually trigger product resend to user.
USER / BUYER:
PRODUCTS:
User should be able to see products, information, images and prices.
User should be able to add and remove products from cart, which is stored in local storage.
ORDERS:
User should be able to request order creation and get an order id.
User should be able to pay for their order (probably Stripe).
User should be able to track their order and see its state.
User should be able to receive the download links again upon their request.
SYSTEM:
System should allow shop owner to login and provide a session token, used for authentication later.
System should verify session token and check if it's revoked or expired.
System should allow users to create orders, get their state, and provide payment methods.
System should check for status changes and automatically send download links.
System should generate snapshots of products and their prices when the order is created (not when payment is provided) — the amount charged to Stripe must match the frozen snapshot, so it has to exist before payment happens.