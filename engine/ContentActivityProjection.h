#pragma once

#include <type_traits>

namespace WebKit {

enum class ContentActivityPolicy : bool { Native, StableBrowsing };

template<typename Activity>
constexpr std::underlying_type_t<Activity> projectContentActivity(
    std::underlying_type_t<Activity> observed, ContentActivityPolicy policy)
{
    using Storage = std::underlying_type_t<Activity>;
    static_assert(std::is_unsigned_v<Storage>);
    constexpr Storage stableFlags = static_cast<Storage>(Activity::WindowIsActive)
        | static_cast<Storage>(Activity::IsFocused)
        | static_cast<Storage>(Activity::IsVisible)
        | static_cast<Storage>(Activity::IsVisibleOrOccluded)
        | static_cast<Storage>(Activity::IsInWindow);
    return policy == ContentActivityPolicy::StableBrowsing
        ? static_cast<Storage>((observed | stableFlags) & ~static_cast<Storage>(Activity::IsVisuallyIdle)) : observed;
}

} // namespace WebKit
