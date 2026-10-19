// 7 inch tablet golden flow: Nexus 7 form factor (logical 1200x1920
// portrait). The adaptive UI uses a master/detail split on this width,
// so captured goldens intentionally exercise that layout rather than
// the phone stack.
//
// Screens captured (in order):
//   1. Home split        -> tablet7_01_home
//   2. Detail with list  -> tablet7_02_detail
//   3. Settings          -> tablet7_03_settings
//   4. Profile           -> tablet7_04_profile
//   5. Paywall modal     -> tablet7_05_paywall
//
// Output files must remain stable: screenshots/compositor.py maps these
// base names to the tablet7 device frame content box.
//
// Execute (via emulator_matrix.py Nexus 7 AVD):
//   flutter test integration_test/tablet7_flow.dart

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

  testWidgets('tablet7_01_home: capture split home layout',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Adaptive home should resolve to the split layout on 1200dp width.
    expect(find.byKey(const ValueKey('HomeSplitLayout')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'tablet7_01_home');
  });

  testWidgets('tablet7_02_detail: capture detail pane with visible list',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // On the split layout the list remains visible; tap the second card.
    final Finder secondCard = find.byKey(const ValueKey('FeedCard_1'));
    expect(secondCard, findsOneWidget);
    await tester.tap(secondCard);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    // Detail pane renders in the right column on tablet7.
    expect(find.byKey(const ValueKey('DetailPane')), findsOneWidget);
    expect(find.byKey(const ValueKey('HomeSplitLayout')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'tablet7_02_detail');
  });

  testWidgets('tablet7_03_settings: capture adaptive settings',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Tablet settings live in a NavigationRail rather than BottomNav.
    final Finder settingsRail = find.byKey(const ValueKey('NavRail_settings'));
    expect(settingsRail, findsOneWidget);
    await tester.tap(settingsRail);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    await tester.scrollUntilVisible(
      find.byKey(const ValueKey('SettingsSection_notifications')),
      120.0,
      scrollable: find.byType(Scrollable).first,
    );
    await _settleAndShoot(tester, binding, 'tablet7_03_settings');
  });

  testWidgets('tablet7_04_profile: capture profile on tablet layout',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    final Finder profileRail = find.byKey(const ValueKey('NavRail_profile'));
    expect(profileRail, findsOneWidget);
    await tester.tap(profileRail);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(find.byKey(const ValueKey('ProfileScreen')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'tablet7_04_profile');
  });

  testWidgets('tablet7_05_paywall: capture paywall on tablet layout',
      (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Navigate through the NavigationRail profile entry to reach the
    // upgrade call to action on the tablet layout.
    final Finder profileRail = find.byKey(const ValueKey('NavRail_profile'));
    expect(profileRail, findsOneWidget);
    await tester.tap(profileRail);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    final Finder upgradeCta = find.byKey(const ValueKey('UpgradeCta'));
    expect(upgradeCta, findsOneWidget);
    await tester.tap(upgradeCta);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(find.byKey(const ValueKey('PaywallScreen')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'tablet7_05_paywall');
  });
}
