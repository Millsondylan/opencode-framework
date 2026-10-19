// Phone golden flow: Pixel 8 form factor (logical 1080x2400, captured
// at device pixel ratio for Play Store 1080x1920 portrait output).
//
// This integration_test harness drives the Flutter application through
// five canonical "golden" screens and captures a real PNG after each
// via IntegrationTestWidgetsFlutterBinding.takeScreenshot. The resulting
// images are the ONLY accepted source for the marketing compositor
// (screenshots/compositor.py); no generative imagery is permitted inside
// the device frame content box.
//
// Screens captured (in order):
//   1. Home        -> phone_01_home
//   2. Detail      -> phone_02_detail
//   3. Settings    -> phone_03_settings
//   4. Profile     -> phone_04_profile
//   5. Paywall     -> phone_05_paywall
//
// Execute (locally or via emulator_matrix.py):
//   flutter test integration_test/phone_flow.dart \
//     --dart-define=SCREENSHOT_PATH=/tmp/captures
//
// Notes for maintainers:
//   * Use tester.pumpAndSettle before each takeScreenshot so animations
//     finish before the pixel grab.
//   * Every navigation step uses real tap or scroll; do not fabricate
//     state through provider overrides.
//   * Screenshot file base names must stay stable because the compositor
//     relies on them.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

// The example app is the driver target. Replace the import below with
// the real application entrypoint when wiring into the host project.
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

  // Android needs this call so takeScreenshot grabs native buffers rather
  // than the semantics tree.
  binding.framePolicy = LiveTestWidgetsFlutterBindingFramePolicy.fullyLive;

  setUp(() async {
    // Nothing per test: each testWidgets boots main() fresh to avoid
    // leaking state between golden captures.
  });

  testWidgets('phone_01_home: capture home screen', (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Verify we are on the expected screen before capturing.
    expect(find.byKey(const ValueKey('HomeScreen')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'phone_01_home');
  });

  testWidgets('phone_02_detail: capture detail screen', (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Tap the first feed item to push the detail route.
    final Finder firstCard = find.byKey(const ValueKey('FeedCard_0'));
    expect(firstCard, findsOneWidget);
    await tester.tap(firstCard);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(find.byKey(const ValueKey('DetailScreen')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'phone_02_detail');
  });

  testWidgets('phone_03_settings: capture settings screen', (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Open the settings tab in the bottom navigation.
    final Finder settingsTab = find.byKey(const ValueKey('NavTab_settings'));
    expect(settingsTab, findsOneWidget);
    await tester.tap(settingsTab);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    // Scroll to reveal the "Appearance" section so the golden includes it.
    await tester.scrollUntilVisible(
      find.byKey(const ValueKey('SettingsSection_appearance')),
      120.0,
      scrollable: find.byType(Scrollable).first,
    );
    await _settleAndShoot(tester, binding, 'phone_03_settings');
  });

  testWidgets('phone_04_profile: capture profile screen', (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    final Finder profileTab = find.byKey(const ValueKey('NavTab_profile'));
    expect(profileTab, findsOneWidget);
    await tester.tap(profileTab);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(find.byKey(const ValueKey('ProfileScreen')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'phone_04_profile');
  });

  testWidgets('phone_05_paywall: capture paywall screen', (WidgetTester tester) async {
    app.main();
    await tester.pumpAndSettle(const Duration(seconds: 3));

    // Navigate: profile -> upgrade button -> paywall modal.
    await tester.tap(find.byKey(const ValueKey('NavTab_profile')));
    await tester.pumpAndSettle(const Duration(seconds: 2));

    final Finder upgradeCta = find.byKey(const ValueKey('UpgradeCta'));
    expect(upgradeCta, findsOneWidget);
    await tester.tap(upgradeCta);
    await tester.pumpAndSettle(const Duration(seconds: 2));

    expect(find.byKey(const ValueKey('PaywallScreen')), findsOneWidget);
    await _settleAndShoot(tester, binding, 'phone_05_paywall');
  });
}
