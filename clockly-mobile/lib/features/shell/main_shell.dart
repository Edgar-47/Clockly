import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../auth/providers/auth_provider.dart';

class MainShell extends ConsumerWidget {
  const MainShell({super.key, required this.child});

  final Widget child;

  static const _adminTabs = [
    _TabItem(
      path: '/attendance',
      icon: Icons.fingerprint_rounded,
      label: 'Jornada',
    ),
    _TabItem(
      path: '/dashboard',
      icon: Icons.grid_view_rounded,
      label: 'Inicio',
    ),
    _TabItem(
      path: '/attendance/history',
      icon: Icons.history_rounded,
      label: 'Historial',
    ),
    _TabItem(
      path: '/employees',
      icon: Icons.groups_rounded,
      label: 'Equipo',
    ),
    _TabItem(
      path: '/settings',
      icon: Icons.person_rounded,
      label: 'Perfil',
    ),
  ];

  static const _employeeTabs = [
    _TabItem(
      path: '/attendance',
      icon: Icons.fingerprint_rounded,
      label: 'Inicio',
    ),
    _TabItem(
      path: '/attendance/history',
      icon: Icons.history_rounded,
      label: 'Historial',
    ),
    _TabItem(
      path: '/tickets',
      icon: Icons.receipt_long_rounded,
      label: 'Tickets',
    ),
    _TabItem(
      path: '/settings',
      icon: Icons.person_rounded,
      label: 'Perfil',
    ),
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).matchedLocation;
    final auth = ref.watch(authProvider).valueOrNull;
    final isAdmin = auth?.session?.activeBusiness?.isAdmin ?? false;
    final tabs = isAdmin ? _adminTabs : _employeeTabs;

    return Scaffold(
      extendBody: true,
      backgroundColor: AppColors.ink,
      body: child,
      bottomNavigationBar: _PremiumBottomNav(
        tabs: tabs,
        selectedIndex: _selectedIndex(location, tabs),
        onSelected: (i) => context.go(tabs[i].path),
      ),
    );
  }

  int _selectedIndex(String location, List<_TabItem> tabs) {
    for (var i = 0; i < tabs.length; i++) {
      final path = tabs[i].path;
      if (location == path) return i;
    }
    for (var i = 0; i < tabs.length; i++) {
      final path = tabs[i].path;
      if (path != '/attendance' && location.startsWith(path)) return i;
    }
    return 0;
  }
}

class _PremiumBottomNav extends StatelessWidget {
  const _PremiumBottomNav({
    required this.tabs,
    required this.selectedIndex,
    required this.onSelected,
  });

  final List<_TabItem> tabs;
  final int selectedIndex;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      minimum: const EdgeInsets.fromLTRB(14, 0, 14, 12),
      child: Container(
        padding: const EdgeInsets.all(6),
        decoration: BoxDecoration(
          color: AppColors.paper.withOpacity(0.96),
          borderRadius: BorderRadius.circular(28),
          border: Border.all(color: Colors.white.withOpacity(0.66)),
          boxShadow: [
            BoxShadow(
              color: AppColors.ink.withOpacity(0.28),
              blurRadius: 28,
              offset: const Offset(0, 14),
            ),
          ],
        ),
        child: Row(
          children: [
            for (var i = 0; i < tabs.length; i++)
              Expanded(
                child: _NavItem(
                  item: tabs[i],
                  selected: selectedIndex == i,
                  onTap: () => onSelected(i),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _NavItem extends StatelessWidget {
  const _NavItem({
    required this.item,
    required this.selected,
    required this.onTap,
  });

  final _TabItem item;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: item.label,
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeOut,
          height: 54,
          padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xs),
          decoration: BoxDecoration(
            color: selected ? AppColors.cobalt : Colors.transparent,
            borderRadius: BorderRadius.circular(22),
          ),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                item.icon,
                size: 21,
                color: selected ? Colors.white : AppColors.neutral500,
              ),
              const SizedBox(height: 3),
              FittedBox(
                fit: BoxFit.scaleDown,
                child: Text(
                  item.label,
                  maxLines: 1,
                  style: TextStyle(
                    color: selected ? Colors.white : AppColors.neutral500,
                    fontSize: 10,
                    fontWeight: selected ? FontWeight.w800 : FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TabItem {
  const _TabItem({
    required this.path,
    required this.icon,
    required this.label,
  });

  final String path;
  final IconData icon;
  final String label;
}
