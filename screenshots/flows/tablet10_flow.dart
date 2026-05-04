// 10 inch tablet golden flow: Pixel Tablet form factor (logical
// 1600x2560 portrait). At this width the application uses the widest
// adaptive layout: persistent NavigationRail on the left, split content
// in the centre, and a secondary context panel on the right for some
// screens. Golden captures exercise each of those compartments.
//
// Screens captured (in order):
//   1. Home (full split)   -> tablet10_01_home
//   2. Detail with context -> tablet10_02_detail
//   3. Settings            -> tablet10_03_settings
//   4. Profile             -> tablet10_04_profile
//   5. Paywall modal       -> tablet10_05_paywall
//
// Output file base names map directly to the tablet10 device frame
// content box defined in screenshots/compositor.py. Do not rename.
//
// Execute (via emulator_matrix.py Pixel Tablet AVD):
//   flutter test integration_test/tablet10_flow.dart

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:example_app/main.dart' as app;

Future<void> _settleAndShoot(
  WidgetTester tester,
  IntegrationTestWidgetsFlutterBinding binding,
  String name,
) async {
  await tester.pumpAndSettle(const Duration(seconds: 3));
  await binding.takeScreenshot(name);
}

void main() {
  final IntegrationTestWidgetsFlutterBinding binding =
      IntegrationTestWidgetsFlutterBinding.ensureInitialized()
          as IntegrationTestWidgetsFlutterBinding;

  binding.framePolicy = LiveTestWidgetsFlutterBindingFramePolicy.fullyLive;

  testWidgets('tablet10_01_home: capture full split home layout',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // The widest adaptive layout uses a three pane composition at this
    // breakpoint: rail, list, detail placeholder.
    expect(find.byKey(const ValueKey('HomeWideLayout')), findsOneWidget);
    expect(find.byKey(const ValueKey('NavRail_home')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'tablet10_01_home');
  });

  testWidgets('tablet10_02_detail: capture detail with context panel',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Tap the third feed card to force the context panel to populate.
    final Finder thirdCard = find.byKey(const ValueKey('FeedCard_2'));
    expect(thirdCard, findsOneWidget);
    await tester.tap(thirdCard);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    // All three panes stay visible at the widest breakpoint.
    expect(find.byKey(const ValueKey('DetailPane')), findsOneWidget);
    expect(find.byKey(const ValueKey('ContextPanel')), findsOneWidget);
    expect(find.byKey(const ValueKey('HomeWideLayout')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'tablet10_02_detail');
  });

  testWidgets('tablet10_03_settings: capture adaptive settings at 10in',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    final Finder settingsRail = find.byKey(const ValueKey('NavRail_settings'));
    expect(settingsRail, findsOneWidget);
    await tester.tap(settingsRail);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    // Settings at 10in shows two columns: category list plus detail.
    expect(find.byKey(const ValueKey('SettingsTwoColumn')), findsOneWidget);
    await tester.scrollUntilVisible(
      find.byKey(const ValueKey('SettingsSection_privacy')),
      160.0,
      scrollable: find.byType(Scrollable).first,
    );
    await _settleAndShoot(tester, binding, 'tablet10_03_settings');
  });

  testWidgets('tablet10_04_profile: capture profile on 10in layout',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    final Finder profileRail = find.byKey(const ValueKey('NavRail_profile'));
    expect(profileRail, findsOneWidget);
    await tester.tap(profileRail);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(find.byKey(const ValueKey('ProfileScreen')), findsOneWidget);
    // Scroll the profile content so the achievements grid enters the frame.
    await tester.scrollUntilVisible(
      find.byKey(const ValueKey('ProfileSection_achievements')),
      200.0,
      scrollable: find.byType(Scrollable).first,
    );
    await _settleAndShoot(tester, binding, 'tablet10_04_profile');
  });

  testWidgets('tablet10_05_paywall: capture paywall modal on 10in',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Navigate: profile rail, then upgrade call to action.
    final Finder profileRail = find.byKey(const ValueKey('NavRail_profile'));
    expect(profileRail, findsOneWidget);
    await tester.tap(profileRail);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    final Finder upgradeCta = find.byKey(const ValueKey('UpgradeCta'));
    expect(upgradeCta, findsOneWidget);
    await tester.tap(upgradeCta);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    // At the 10in width the paywall renders as a centred dialog rather
    // than a full screen route.
    expect(find.byKey(const ValueKey('PaywallScreen')), findsOneWidget);
    expect(find.byKey(const ValueKey('PaywallDialog')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'tablet10_05_paywall');
  });
}
