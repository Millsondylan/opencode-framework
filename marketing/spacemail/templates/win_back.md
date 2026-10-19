# {{first_name}}, we missed you. Here is what changed in {{app_name}}

## HTML body

```html
<div style="font-family: system-ui, sans-serif; max-width: 560px; margin: 0 auto; color: #222;">
  <h2 style="margin-top: 0;">It has been a while, {{first_name}}.</h2>

  <p>
    You last opened {{app_name}} more than 60 days ago. We have
    shipped a lot since then, and we would love to show you what is
    new. If none of this lands, the unsubscribe link at the bottom is
    one click.
  </p>

  <h3>Three things that are different</h3>
  <ul>
    <li>
      <strong>Offline first rebuild.</strong> Every screen now works
      with zero network. Sync happens in the background when you are
      back online.
    </li>
    <li>
      <strong>Calm notifications.</strong> We cut push notifications by
      80 percent. The only pings you get now are ones you asked for.
    </li>
    <li>
      <strong>Faster review.</strong> The review tab renders 10 times
      faster and supports bulk actions for the first time.
    </li>
  </ul>

  <h3>A small thank you</h3>
  <p>
    For coming back, we are extending your account by 30 days of the
    paid tier at no cost. The credit lands the moment you open the
    app. No coupon code, no checkout.
  </p>

  <p>
    <a
      href="{{unsubscribe_url}}"
      style="color: #666; font-size: 12px;"
    >
      Prefer no more emails? One click unsubscribe here.
    </a>
  </p>

  <p style="margin-top: 24px;">
    See you soon,<br>
    The {{company_name}} team
  </p>
</div>
```

## Plain text body

It has been a while, {{first_name}}.

You last opened {{app_name}} more than 60 days ago. We have shipped
a lot since then, and we would love to show you what is new. If none
of this lands, the unsubscribe link at the bottom is one click.

Three things that are different:

  1. Offline first rebuild. Every screen now works with zero network.
     Sync happens in the background when you are back online.

  2. Calm notifications. We cut push notifications by 80 percent. The
     only pings you get now are ones you asked for.

  3. Faster review. The review tab renders 10 times faster and supports
     bulk actions for the first time.

A small thank you:
For coming back, we are extending your account by 30 days of the paid
tier at no cost. The credit lands the moment you open the app. No
coupon code, no checkout.

See you soon,
The {{company_name}} team

Prefer no more emails? One click unsubscribe: {{unsubscribe_url}}

{{postal_address}}
