import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../shared/widgets/brand_logo.dart';
import '../auth/providers/auth_provider.dart';

class MainShell extends ConsumerWidget {
  const MainShell({super.key, required this.child});

  final Widget child;

  static const _tabs = [
    _TabItem(
      path: '/attendance',
      icon: Icons.fingerprint_rounded,
      label: 'Fichaje',
      usesBrandMark: true,
    ),
    _TabItem(
      path: '/dashboard',
      icon: Icons.dashboard_rounded,
      label: 'Dashboard',
    ),
    _TabItem(path: '/employees', icon: Icons.people_rounded, label: 'Equipo'),
    _TabItem(
      path: '/tickets',
      icon: Icons.receipt_long_rounded,
      label: 'Tickets',
    ),
    _TabItem(path: '/settings', icon: Icons.settings_rounded, label: 'Config'),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).matchedLocation;
    final auth = ref.watch(authProvider).valueOrNull;
    final isAdmin = auth?.session?.activeBusiness?.isAdmin ?? false;

    final visibleTabs = isAdmin
        ? _tabs
        : _tabs.where((t) => t.path != '/employees').toList();

    return Scaffold(
      body: child,
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          color: AppColors.surface,
          border: Border(top: BorderSide(color: AppColors.neutral200)),
        ),
        child: NavigationBar(
          selectedIndex: _visibleIndex(location, visibleTabs),
          onDestinationSelected: (i) {
            context.go(visibleTabs[i].path);
          },
          destinations: visibleTabs
              .map(
                (tab) => NavigationDestination(
                  icon: tab.usesBrandMark
                      ? const ClocklyBrandLogo(
                          variant: ClocklyLogoVariant.mark,
                          markSize: 24,
                        )
                      : Icon(tab.icon),
                  selectedIcon: tab.usesBrandMark
                      ? const ClocklyBrandLogo(
                          variant: ClocklyLogoVariant.mark,
                          markSize: 26,
                        )
                      : Icon(tab.icon),
                  label: tab.label,
                ),
              )
              .toList(),
        ),
      ),
    );
  }

  int _tabIndexFor(String location) {
    for (var i = 0; i < _tabs.length; i++) {
      if (location.startsWith(_tabs[i].path)) return i;
    }
    return 0;
  }

  int _visibleIndex(String location, List<_TabItem> tabs) {
    for (var i = 0; i < tabs.length; i++) {
      if (location.startsWith(tabs[i].path)) return i;
    }
    return 0;
  }
}

class _TabItem {
  const _TabItem({
    required this.path,
    required this.icon,
    required this.label,
    this.usesBrandMark = false,
  });

  final String path;
  final IconData icon;
  final String label;
  final bool usesBrandMark;
}
