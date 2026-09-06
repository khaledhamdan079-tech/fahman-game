import 'package:fahman/features/match_setup/presentation/setup_controller.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('random category selection respects the requested count', () {
    final container = ProviderContainer();
    addTearDown(container.dispose);
    final controller = container.read(setupControllerProvider.notifier);

    controller.setCount(5);
    controller.selectRandom(demoCategories);

    final state = container.read(setupControllerProvider);
    expect(state.selected, hasLength(5));
    expect(
      state.selected.every(
        (id) => demoCategories.any((item) => item.id == id && item.eligible),
      ),
      isTrue,
    );
  });
}
